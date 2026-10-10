"""Correction-quality evaluation. For each case:
  1. Ingest the company guidelines into a throw-away Postgres (real Gemini embeddings).
  2. Answer a similar customer message WITHOUT any correction stored (baseline).
  3. Store the agent's thumbs-down correction for the original message.
  4. Answer the similar message again WITH the correction retrievable.
  5. Ask Gemini, as a judge, to score both answers 1-5 for closeness to the corrected answer.

  GEMINI_API_KEY=... uv run python -m eval.corrections_eval [--repeats 3]

Pin the judge with EVAL_JUDGE_MODEL when comparing chat models so a candidate does not grade
itself. Writes docs/evals/corrections-results.json and docs/evals/corrections-results.md."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.auth.users import seed_users
from app.config import load_config, load_dotenv_if_present
from app.conversations.service import ConversationsService
from app.db.models import Company, User
from app.feedback.service import FeedbackService, SubmitFeedbackInput
from app.guidelines.service import GuidelinesService, UploadInput
from app.ingestion.job import IngestionJob
from app.jobs.queue import INGEST_GUIDELINES, InMemoryQueue
from app.logging import configure_logging, get_logger
from app.main import build_deps
from app.observability.tracer import create_noop_tracer
from app.rag.embeddings import GeminiEmbedder
from app.rag.llm import GeminiChatModel
from app.schemas import FeedbackRating, MessageKind, MessageStatus
from eval.evaldb import EvalPostgres

HERE = Path(__file__).resolve().parent
SEED = HERE.parent / "seed" / "guidelines"
OUT = HERE.parents[1] / "docs" / "evals"


@dataclass
class Verdict:
    score: int
    reason: str


@dataclass
class ArmResult:
    reply: str
    score: float
    scores: list[int]
    reason: str
    correctionsUsed: int


@dataclass
class CaseResult:
    company: str
    similarMessage: str
    baseline: ArmResult
    withCorrection: ArmResult


@dataclass
class Answer:
    id: str
    content: str
    corrections_used: int


async def judge_answer(
    client: Any, model: str, customer: str, target: str, candidate: str
) -> Verdict:
    from google.genai import types

    res = await client.aio.models.generate_content(
        model=model,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text="\n\n".join(
                            [
                                "You grade customer-support replies. Compare the CANDIDATE reply with the REFERENCE reply a senior agent wrote for the same kind of request.",
                                "Score 1-5: 5 = same steps, commitments and tone; 3 = right direction but missing a key step or commitment; 1 = contradicts or ignores the reference.",
                                f"CUSTOMER MESSAGE:\n{customer}\n\nREFERENCE:\n{target}\n\nCANDIDATE:\n{candidate}",
                            ]
                        )
                    )
                ],
            )
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {"score": {"type": "INTEGER"}, "reason": {"type": "STRING"}},
                "required": ["score", "reason"],
            },
            temperature=0,
        ),
    )
    data = json.loads(res.text or "{}")
    score = int(data["score"])
    if not 1 <= score <= 5:
        raise ValueError(f"judge score out of range: {score}")
    return Verdict(score=score, reason=str(data["reason"]))


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=1)
    args = parser.parse_args()
    repeats = max(1, args.repeats)

    load_dotenv_if_present()
    config = load_config(
        {**os.environ, "DATABASE_URL": "postgres://unused", "JWT_SECRET": "eval-secret-0123456789"}
    )
    configure_logging("warn")
    log = get_logger("eval")
    dataset = json.loads((HERE / "corrections-dataset.json").read_text())

    embedder = GeminiEmbedder(
        api_key=config.GEMINI_API_KEY,
        model=config.GEMINI_EMBEDDING_MODEL,
        dimensions=config.GEMINI_EMBEDDING_DIMENSIONS,
        log=log,
    )
    chat_model = GeminiChatModel(
        api_key=config.GEMINI_API_KEY,
        model=config.GEMINI_CHAT_MODEL,
        thinking_level=config.GEMINI_THINKING_LEVEL,
        log=log,
    )
    from google import genai

    judge = genai.Client(api_key=config.GEMINI_API_KEY)
    judge_model = os.environ.get("EVAL_JUDGE_MODEL") or config.GEMINI_CHAT_MODEL

    pg = EvalPostgres()
    results: list[CaseResult] = []
    try:
        for c in dataset["cases"]:
            async with pg.database() as sessions:
                queue = InMemoryQueue()
                deps = build_deps(
                    config,
                    sessions=sessions,
                    queue=queue,
                    embedder=embedder,
                    chat_model=chat_model,
                    tracer=create_noop_tracer(),
                    log=log,
                )
                ingest = IngestionJob(deps)

                async def handler(
                    payload: dict[str, Any], job_id: str, ingest: IngestionJob = ingest
                ) -> None:
                    await ingest.run(payload)

                await queue.subscribe(INGEST_GUIDELINES, handler)
                async with sessions() as session:
                    await seed_users(session, "agent1:agent1pass")
                    user = await session.scalar(select(User))
                    assert user is not None
                    user_id = str(user.id)
                    company = Company(name=c["company"], created_by=user.id)
                    session.add(company)
                    await session.commit()
                    company_id = str(company.id)
                    await GuidelinesService(
                        session, queue, max_upload_bytes=10 * 1024 * 1024
                    ).upload(
                        UploadInput(
                            company_id=company_id,
                            filename=c["file"],
                            body=(SEED / c["file"]).read_bytes(),
                            user_id=user_id,
                        )
                    )
                await queue.drain()

                async def ask(text: str) -> Answer:
                    async with sessions() as session:
                        conversations = ConversationsService(session, deps)
                        conv = await conversations.create(company_id, user_id)
                        conversation_id = conv.summary.id
                        sent = await conversations.send_message(
                            conversation_id=conversation_id,
                            kind=MessageKind.customer,
                            content=text,
                            user_id=user_id,
                        )
                        a = sent.assistant_message
                        # Provider hiccups (rate limits, transient 5xx) would otherwise skew the comparison: retry like an agent would.
                        attempt = 1
                        while a.status == MessageStatus.failed and attempt <= 3:
                            print(
                                f"  answer failed ({a.error or 'unknown'}), retry {attempt}/3",
                                file=sys.stderr,
                            )
                            await asyncio.sleep(2 * attempt)
                            sent = await conversations.send_message(
                                conversation_id=conversation_id,
                                kind=MessageKind.customer,
                                content=text,
                                user_id=user_id,
                            )
                            a = sent.assistant_message
                            attempt += 1
                        if a.status == MessageStatus.failed:
                            raise RuntimeError(
                                f"answer failed after retries: {a.error or 'unknown'}"
                            )
                        return Answer(
                            id=a.id,
                            content=a.content,
                            corrections_used=len(a.correctionsUsed or []),
                        )

                # Baseline: answer the similar message N times with no corrections stored.
                baselines = [await ask(c["similarMessage"]) for _ in range(repeats)]
                # Store the correction against an answer to the original message.
                original = await ask(c["message"])
                async with sessions() as session:
                    await FeedbackService(session, deps).submit(
                        SubmitFeedbackInput(
                            message_id=original.id,
                            rating=FeedbackRating.down,
                            what_was_wrong=c["whatWasWrong"],
                            corrected_answer=c["correctedAnswer"],
                            user_id=user_id,
                        )
                    )
                # Answer the similar message again; the correction should now be retrieved.
                improved = [await ask(c["similarMessage"]) for _ in range(repeats)]

                async def judged(answers: list[Answer]) -> list[Verdict]:
                    return [
                        await judge_answer(
                            judge, judge_model, c["similarMessage"], c["correctedAnswer"], a.content
                        )
                        for a in answers
                    ]

                bj, wj = await judged(baselines), await judged(improved)
                mean = lambda xs: sum(xs) / len(xs)  # noqa: E731
                b = ArmResult(
                    reply=baselines[0].content,
                    score=mean([v.score for v in bj]),
                    scores=[v.score for v in bj],
                    reason=bj[0].reason,
                    correctionsUsed=baselines[0].corrections_used,
                )
                w = ArmResult(
                    reply=improved[0].content,
                    score=mean([v.score for v in wj]),
                    scores=[v.score for v in wj],
                    reason=wj[0].reason,
                    correctionsUsed=min(a.corrections_used for a in improved),
                )
                results.append(CaseResult(c["company"], c["similarMessage"], b, w))
                print(
                    f"[{c['company']}] baseline {b.score:.2f} → with correction {w.score:.2f} (corrections retrieved: {w.correctionsUsed})",
                    file=sys.stderr,
                )
    finally:
        pg.stop()

    avg = lambda xs: sum(xs) / len(xs)  # noqa: E731
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    md = [
        "# Correction-quality evaluation results",
        "",
        f"Generated {now} with chat model `{config.GEMINI_CHAT_MODEL}`, embeddings `{config.GEMINI_EMBEDDING_MODEL}` ({config.GEMINI_EMBEDDING_DIMENSIONS}d), RAG_CORRECTIONS_MIN_SCORE = {config.RAG_CORRECTIONS_MIN_SCORE}, {repeats} sample(s) per arm, thinking `{config.GEMINI_THINKING_LEVEL}`, judge = `{judge_model}` at temperature 0. Scores are judge means over the samples (individual samples in brackets).",
        "",
        "| Case | Corrections retrieved | Baseline score | With correction |",
        "|---|---|---|---|",
        *[
            f"| [{r.company}] {r.similarMessage} | {r.withCorrection.correctionsUsed} | {r.baseline.score:.2f} [{', '.join(map(str, r.baseline.scores))}] | {r.withCorrection.score:.2f} [{', '.join(map(str, r.withCorrection.scores))}] |"
            for r in results
        ],
        f"| **Average** | | **{avg([r.baseline.score for r in results]):.2f}** | **{avg([r.withCorrection.score for r in results]):.2f}** |",
        "",
        "## Details",
        "",
    ]
    for r in results:
        md += [
            f"### [{r.company}] {r.similarMessage}",
            "",
            f"**Baseline ({r.baseline.score:.2f}/5)** — {r.baseline.reason}",
            "",
            "> " + r.baseline.reply.replace("\n", "\n> "),
            "",
            f"**With correction ({r.withCorrection.score:.2f}/5)** — {r.withCorrection.reason}",
            "",
            "> " + r.withCorrection.reply.replace("\n", "\n> "),
            "",
        ]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "corrections-results.json").write_text(
        json.dumps({"generatedAt": now, "results": [asdict(r) for r in results]}, indent=2)
    )
    (OUT / "corrections-results.md").write_text("\n".join(md))
    print("wrote docs/evals/corrections-results.{json,md}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
