"""Retrieval evaluation: for each labelled customer message, does the expected guideline section
rank first (for multi-topic messages: do all expected sections reach the prompt)? How well does
the similarity threshold separate in-scope from out-of-scope? Does the keyword rescue bring back
sections the vector ranking missed, and how often does it misfire?
Vector and hybrid rankings run in memory (chunker + real Gemini embeddings); the keyword rescue
runs the production SQL on a throw-away Postgres, at the production dimension only.

  GEMINI_API_KEY=... uv run python -m eval.retrieval_eval [--dims 768,1536] [--thresholds 0.45,0.5,...]

Writes docs/evals/retrieval-results.json and docs/evals/retrieval-results.md."""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from app.config import load_dotenv_if_present
from app.db.models import EMBEDDING_DIMENSIONS, Company, GuidelineChunk, GuidelineVersion, User
from app.ingestion.chunker import Chunk, chunk_text
from app.logging import configure_logging, get_logger
from app.rag.embeddings import GeminiEmbedder
from app.rag.retrieval import retrieve_keyword_rescue
from app.schemas import GuidelineStatus
from eval.evaldb import EvalPostgres

HERE = Path(__file__).resolve().parent
SEED = HERE.parent / "seed" / "guidelines"
OUT = HERE.parents[1] / "docs" / "evals"
STYLES = ("original", "manual", "vague", "multi")


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def create_bm25(docs: list[str]):  # type: ignore[no-untyped-def]
    """Minimal BM25 (k1 = 1.2, b = 0.75) over lower-cased alphanumeric tokens; stands in for
    Postgres full-text search."""
    tokenize = lambda s: re.findall(r"[a-z0-9]+", s.lower())  # noqa: E731
    tokens = [tokenize(d) for d in docs]
    avg_len = sum(len(d) for d in tokens) / max(1, len(tokens))
    df: Counter[str] = Counter()
    for d in tokens:
        df.update(set(d))
    n = len(docs)

    def score(query: str) -> list[float]:
        q = set(tokenize(query))
        out = []
        for d in tokens:
            tf = Counter(d)
            s = 0.0
            for term in q:
                f = tf.get(term)
                if not f:
                    continue
                idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
                s += idf * (f * 2.2) / (f + 1.2 * (1 - 0.75 + 0.75 * len(d) / avg_len))
            out.append(s)
        return out

    return score


def rrf(rankings: list[list[int]], size: int) -> list[tuple[int, float]]:
    """Reciprocal-rank fusion (k = 60) of rankings given as ordered index lists."""
    scores = [0.0] * size
    for ranking in rankings:
        for rank, index in enumerate(ranking):
            scores[index] += 1 / (60 + rank)
    return sorted(enumerate(scores), key=lambda x: -x[1])


@dataclass
class Ranked:
    title: str
    score: float


@dataclass
class HybridRanked:
    title: str
    rrf: float


@dataclass
class QueryResult:
    company: str
    text: str
    expected: str
    expectedAll: list[str]
    style: str
    ranked: list[Ranked]
    expectedScore: float
    bestScore: float
    top1: bool
    top3: bool
    topK: bool
    margin: float
    hybridRanked: list[HybridRanked]
    hybridTop1: bool
    hybridTop3: bool
    hybridTopK: bool
    rescueTitle: str | None = None
    rescueTopK: bool | None = None
    rescueEvaluated: bool = False


@dataclass
class ProbeResult:
    company: str
    text: str
    best: Ranked
    rescueTitle: str | None = None


@dataclass
class StyleSummary:
    total: int
    top1Accuracy: float
    topKRecall: float
    rescueTopKRecall: float | None


@dataclass
class ThresholdRow:
    threshold: float
    inScopePassGate: int
    inScopeExpectedKept: int
    inScopeTotal: int
    outOfScopeRejected: int
    outOfScopeTotal: int


@dataclass
class RescueSummary:
    topKRecall: float
    fired: int
    genuine: int
    redundant: int
    wrong: int
    probesFired: int


@dataclass
class DimResult:
    dims: int
    queries: list[QueryResult]
    probes: list[ProbeResult]
    top1Accuracy: float
    top3Recall: float
    topKRecall: float
    hybridTop1Accuracy: float
    hybridTop3Recall: float
    hybridTopKRecall: float
    meanMargin: float
    minMargin: float
    byStyle: dict[str, StyleSummary]
    rescue: RescueSummary | None
    thresholds: list[ThresholdRow] = field(default_factory=list)


class RescueFixture:
    """The production keyword rescue needs the real table (generated tsvector column), so the
    chunks and their vectors are loaded into a migrated throw-away database."""

    def __init__(self, sessions: Any) -> None:
        self.sessions = sessions
        self.user_id: UUID | None = None

    async def load_company(
        self, name: str, file_bytes: bytes, chunks: list[Chunk], vectors: list[list[float]]
    ) -> tuple[UUID, dict[int, UUID]]:
        async with self.sessions() as session:
            if self.user_id is None:
                user = User(username="eval", password_hash="n/a", display_name="Eval")
                session.add(user)
                await session.flush()
                self.user_id = user.id
            company = Company(name=name, created_by=self.user_id)
            session.add(company)
            await session.flush()
            version = GuidelineVersion(
                company_id=company.id,
                filename=f"{name}.txt",
                content_type="text/plain",
                size_bytes=len(file_bytes),
                sha256="eval",
                file_bytes=file_bytes,
                status=GuidelineStatus.ready,
                chunks_total=len(chunks),
                chunks_embedded=len(chunks),
                created_by=self.user_id,
            )
            session.add(version)
            await session.flush()
            rows = [
                GuidelineChunk(
                    version_id=version.id,
                    company_id=company.id,
                    ordinal=c.ordinal,
                    title=c.title,
                    content=c.content,
                    token_count=c.tokenCount,
                    embedding=v,
                )
                for c, v in zip(chunks, vectors, strict=True)
            ]
            session.add_all(rows)
            await session.commit()
            return version.id, {r.ordinal: r.id for r in rows}

    async def rescue(
        self,
        version_id: UUID,
        id_by_ordinal: dict[int, UUID],
        chunks: list[Chunk],
        query: str,
        vector: list[float],
        top_indexes: list[int],
    ) -> str | None:
        async with self.sessions() as session:
            hit = await retrieve_keyword_rescue(
                session,
                version_id=version_id,
                query=query,
                vector=vector,
                exclude=[str(id_by_ordinal[chunks[i].ordinal]) for i in top_indexes],
            )
        return (hit.title or "") if hit else None


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dims", default="768,1536")
    parser.add_argument("--top-k", type=int, default=4)  # RAG_TOP_K: sections the model sees
    parser.add_argument("--thresholds", default="0.5,0.55,0.58,0.6,0.62,0.65,0.7")
    args = parser.parse_args()
    dims = [int(x) for x in args.dims.split(",")]
    top_k = args.top_k
    thresholds = [float(x) for x in args.thresholds.split(",")]

    load_dotenv_if_present()
    import os

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY is required (set it in .env or the environment)")
    model = os.environ.get("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2")
    configure_logging("warn")
    log = get_logger("eval")
    dataset = json.loads((HERE / "retrieval-dataset.json").read_text())

    pg = EvalPostgres()
    results: list[DimResult] = []
    try:
        for d in dims:
            embedder = GeminiEmbedder(api_key=api_key, model=model, dimensions=d, log=log)
            use_fixture = d == EMBEDDING_DIMENSIONS
            async with pg.database() as sessions:
                fixture = RescueFixture(sessions) if use_fixture else None
                queries: list[QueryResult] = []
                probes: list[ProbeResult] = []
                for company, spec in dataset["companies"].items():
                    file_bytes = (SEED / spec["file"]).read_bytes()
                    chunks = chunk_text(file_bytes.decode("utf-8"))
                    texts = [f"{c.title}\n{c.content}" if c.title else c.content for c in chunks]
                    vectors = await embedder.embed_documents(texts)
                    titles = [c.title or f"#{c.ordinal}" for c in chunks]
                    bm25 = create_bm25(texts)
                    loaded = (
                        await fixture.load_company(company, file_bytes, chunks, vectors)
                        if fixture
                        else None
                    )

                    async def rank(q: str) -> tuple[list[float], list[tuple[int, str, float]]]:
                        qv = await embedder.embed_query(q)
                        ranked = sorted(
                            ((i, titles[i], dot(qv, vectors[i])) for i in range(len(chunks))),
                            key=lambda x: -x[2],
                        )
                        return qv, ranked

                    async def do_rescue(
                        text: str, qv: list[float], ranked: list[tuple[int, str, float]]
                    ) -> str | None:
                        assert fixture and loaded
                        return await fixture.rescue(
                            loaded[0], loaded[1], chunks, text, qv, [r[0] for r in ranked[:top_k]]
                        )

                    for q in spec["queries"]:
                        expected_all = (
                            q["expected"] if isinstance(q["expected"], list) else [q["expected"]]
                        )
                        for e in expected_all:
                            if e not in titles:
                                raise SystemExit(f'[{company}] unknown expected section "{e}"')
                        qv, ranked = await rank(q["text"])
                        is_expected = lambda t, ea=expected_all: t in ea  # noqa: E731
                        all_in = lambda top, ea=expected_all: all(
                            any(t == e for t in top) for e in ea
                        )  # noqa: E731
                        by_title = {t: s for _, t, s in ranked}
                        expected_score = min(by_title.get(e, 0.0) for e in expected_all)
                        best_unexpected = next((s for _, t, s in ranked if not is_expected(t)), 0.0)
                        lexical = [
                            i
                            for i, s in sorted(
                                ((i, s) for i, s in enumerate(bm25(q["text"])) if s > 0),
                                key=lambda x: -x[1],
                            )
                        ]
                        hybrid = [
                            (titles[i], s)
                            for i, s in rrf([[r[0] for r in ranked], lexical], len(chunks))
                        ]
                        top_titles = [t for _, t, _ in ranked[:top_k]]
                        in_top_k = all_in(top_titles)
                        rescued: str | None = None
                        rescue_top_k: bool | None = None
                        if loaded:
                            rescued = await do_rescue(q["text"], qv, ranked)
                            rescue_top_k = all_in([*top_titles, *([rescued] if rescued else [])])
                        queries.append(
                            QueryResult(
                                company=company,
                                text=q["text"],
                                expected=" + ".join(expected_all),
                                expectedAll=expected_all,
                                style="multi"
                                if len(expected_all) > 1
                                else q.get("style", "original"),
                                ranked=[Ranked(t, s) for _, t, s in ranked[:5]],
                                expectedScore=expected_score,
                                bestScore=ranked[0][2] if ranked else 0.0,
                                top1=is_expected(ranked[0][1]) if ranked else False,
                                top3=all_in([t for _, t, _ in ranked[:3]]),
                                topK=in_top_k,
                                margin=expected_score - best_unexpected,
                                hybridRanked=[HybridRanked(t, s) for t, s in hybrid[:5]],
                                hybridTop1=is_expected(hybrid[0][0]) if hybrid else False,
                                hybridTop3=all_in([t for t, _ in hybrid[:3]]),
                                hybridTopK=all_in([t for t, _ in hybrid[:top_k]]),
                                rescueTitle=rescued,
                                rescueTopK=rescue_top_k,
                                rescueEvaluated=loaded is not None,
                            )
                        )
                    for p in spec["outOfScope"]:
                        qv, ranked = await rank(p)
                        probes.append(
                            ProbeResult(
                                company=company,
                                text=p,
                                best=Ranked(ranked[0][1], ranked[0][2]),
                                rescueTitle=await do_rescue(p, qv, ranked) if loaded else None,
                            )
                        )

            def ratio(xs: list[QueryResult], pred: Any) -> float:
                return len([q for q in xs if pred(q)]) / len(xs) if xs else 0.0

            def summarise(xs: list[QueryResult]) -> StyleSummary:
                return StyleSummary(
                    total=len(xs),
                    top1Accuracy=ratio(xs, lambda q: q.top1),
                    topKRecall=ratio(xs, lambda q: q.topK),
                    rescueTopKRecall=ratio(xs, lambda q: q.rescueTopK is True)
                    if use_fixture
                    else None,
                )

            r = DimResult(
                dims=d,
                queries=queries,
                probes=probes,
                top1Accuracy=ratio(queries, lambda q: q.top1),
                top3Recall=ratio(queries, lambda q: q.top3),
                topKRecall=ratio(queries, lambda q: q.topK),
                hybridTop1Accuracy=ratio(queries, lambda q: q.hybridTop1),
                hybridTop3Recall=ratio(queries, lambda q: q.hybridTop3),
                hybridTopKRecall=ratio(queries, lambda q: q.hybridTopK),
                meanMargin=sum(q.margin for q in queries) / len(queries),
                minMargin=min(q.margin for q in queries),
                byStyle={s: summarise([q for q in queries if q.style == s]) for s in STYLES},
                rescue=RescueSummary(
                    topKRecall=ratio(queries, lambda q: q.rescueTopK is True),
                    fired=len([q for q in queries if q.rescueTitle]),
                    genuine=len([q for q in queries if not q.topK and q.rescueTopK]),
                    redundant=len([q for q in queries if q.topK and q.rescueTitle]),
                    wrong=len(
                        [q for q in queries if not q.topK and q.rescueTitle and not q.rescueTopK]
                    ),
                    probesFired=len([p for p in probes if p.rescueTitle]),
                )
                if use_fixture
                else None,
                thresholds=[
                    ThresholdRow(
                        threshold=t,
                        inScopePassGate=len([q for q in queries if q.bestScore >= t]),
                        inScopeExpectedKept=len([q for q in queries if q.expectedScore >= t]),
                        inScopeTotal=len(queries),
                        outOfScopeRejected=len([p for p in probes if p.best.score < t]),
                        outOfScopeTotal=len(probes),
                    )
                    for t in thresholds
                ],
            )
            results.append(r)
            line = (
                f"dims={d}: top1={r.top1Accuracy * 100:.1f}% top3={r.top3Recall * 100:.1f}% "
                f"top{top_k}={r.topKRecall * 100:.1f}% | hybrid top1={r.hybridTop1Accuracy * 100:.1f}% "
                f"top3={r.hybridTop3Recall * 100:.1f}% top{top_k}={r.hybridTopKRecall * 100:.1f}%"
            )
            if r.rescue:
                line += (
                    f" | rescue top{top_k}={r.rescue.topKRecall * 100:.1f}% fired={r.rescue.fired} "
                    f"genuine={r.rescue.genuine} redundant={r.rescue.redundant} wrong={r.rescue.wrong} "
                    f"probesFired={r.rescue.probesFired}"
                )
            print(line, file=sys.stderr)
    finally:
        pg.stop()

    write_report(results, dataset, model, top_k)


def pct(n: float) -> str:
    return f"{n * 100:.1f}%"


def write_report(results: list[DimResult], dataset: dict[str, Any], model: str, top_k: int) -> None:
    first = results[0]
    style_counts = ", ".join(f"{first.byStyle[s].total} {s}" for s in STYLES)
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    md: list[str] = [
        "# Retrieval evaluation results",
        "",
        f"Generated {now} with model `{model}`, chunker defaults, cosine similarity on unit vectors.",
        "",
        f"Dataset: {len(first.queries)} labelled in-scope messages ({style_counts}) and {len(first.probes)} out-of-scope probes across {len(dataset['companies'])} companies. Styles: original = the first labelled set; manual = the acceptance test plans; vague = short, emotional or underspecified messages; multi = messages spanning two sections, counted as recalled only when both reach the prompt.",
        "",
        "## Ranking quality",
        "",
        f"| Dimensions | Top-1 accuracy | Top-3 recall | Top-{top_k} recall (in prompt) | Mean margin | Min margin | Hybrid top-1 | Hybrid top-3 | Hybrid top-{top_k} | Top-{top_k} + keyword rescue |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        md.append(
            f"| {r.dims} | {pct(r.top1Accuracy)} | {pct(r.top3Recall)} | {pct(r.topKRecall)} | {r.meanMargin:.3f} | {r.minMargin:.3f} | {pct(r.hybridTop1Accuracy)} | {pct(r.hybridTop3Recall)} | {pct(r.hybridTopKRecall)} | {pct(r.rescue.topKRecall) if r.rescue else 'n/a'} |"
        )
    md += [
        "",
        f"Top-{top_k} recall is the metric that matters in production: RAG_TOP_K sections go into the prompt, so the model sees the expected section whenever it is in the top {top_k}. ",
        "Margin = similarity of the (weakest) expected section minus the best other section; higher means the ranking is more robust. Hybrid = reciprocal-rank fusion (k = 60) of the cosine ranking and an in-memory BM25 ranking over the same chunks, i.e. what a Postgres full-text + pgvector hybrid would do. Keyword rescue = the production query (Postgres full-text, English stemming) that appends one section containing a distinctive, repeated word of the message when the vector top-k missed it; it never reorders the vector ranking, so top-1 is unchanged by construction.",
        "",
        "## By query style",
        "",
    ]
    for r in results:
        md += [
            f"### {r.dims} dimensions",
            "",
            f"| Style | Queries | Top-1 accuracy | Top-{top_k} recall | Top-{top_k} + keyword rescue |",
            "|---|---|---|---|---|",
        ]
        for s in STYLES:
            b = r.byStyle[s]
            md.append(
                f"| {s} | {b.total} | {pct(b.top1Accuracy)} | {pct(b.topKRecall)} | {pct(b.rescueTopKRecall) if b.rescueTopKRecall is not None else 'n/a'} |"
            )
        md.append("")
    md += ["## Keyword rescue", ""]
    for r in results:
        md += [f"### {r.dims} dimensions", ""]
        if not r.rescue:
            md += ["Not evaluated (schema column is vector(768)).", ""]
            continue
        md += [
            f"Fired on {r.rescue.fired}/{len(r.queries)} in-scope messages: {r.rescue.genuine} genuine (an expected section missed by vectors, brought back), {r.rescue.redundant} redundant (expected sections already in the prompt; one extra section), {r.rescue.wrong} wrong (an expected section missed and a different one appended). Fired on {r.rescue.probesFired}/{len(r.probes)} out-of-scope probes.",
            "",
        ]
        genuine = [q for q in r.queries if not q.topK and q.rescueTopK]
        if genuine:
            md += [
                "Genuine rescues:",
                "",
                *[f'- [{q.company}] "{q.text}" → **{q.rescueTitle}**' for q in genuine],
                "",
            ]
        other = [q for q in r.queries if q.rescueTitle and not (q.rescueTopK and not q.topK)]
        if other:
            md += [
                "Rescue appended a section that was not needed or not the missing one:",
                "",
                *[
                    f'- [{q.company}] "{q.text}" → appended **{q.rescueTitle}** (expected {q.expected} {"already in prompt" if q.topK else "STILL MISSING"})'
                    for q in other
                ],
                "",
            ]
        fired = [p for p in r.probes if p.rescueTitle]
        if fired:
            md += [
                "Out-of-scope probes where the rescue fired:",
                "",
                *[f'- [{p.company}] "{p.text}" → {p.rescueTitle}' for p in fired],
                "",
            ]
        else:
            md += ["The rescue did not fire on any out-of-scope probe.", ""]
    md += [
        "## Coverage gate (RAG_MIN_SCORE)",
        "",
        "Pass gate = in-scope messages where at least one section clears the threshold, i.e. the server lets the model answer (should be all). Expected kept = every expected section itself clears it. Out-of-scope rejected = probes whose best section scores below the threshold (should be all).",
        "",
    ]
    for r in results:
        md += [
            f"### {r.dims} dimensions",
            "",
            "| Threshold | In-scope pass gate | Expected section kept | Out-of-scope rejected |",
            "|---|---|---|---|",
        ]
        for t in r.thresholds:
            md.append(
                f"| {t.threshold} | {t.inScopePassGate}/{t.inScopeTotal} | {t.inScopeExpectedKept}/{t.inScopeTotal} | {t.outOfScopeRejected}/{t.outOfScopeTotal} |"
            )
        md.append("")
    md += ["## Misses and closest calls", ""]
    for r in results:
        md += [f"### {r.dims} dimensions", ""]
        misses = [q for q in r.queries if not q.top1]
        if misses:
            md += [
                "Top-1 misses:",
                "",
                *[
                    f'- [{q.company}, {q.style}] "{q.text}" → expected **{q.expected}**, got **{q.ranked[0].title}** ({q.ranked[0].score:.3f})'
                    for q in misses
                ],
                "",
            ]
        else:
            md += ["No top-1 misses.", ""]
        md += ["Smallest margins:", ""]
        for q in sorted(r.queries, key=lambda q: q.margin)[:5]:
            other_ = next((x for x in q.ranked if x.title not in q.expectedAll), None)
            md.append(
                f'- {q.margin:.3f} [{q.company}] "{q.text}" ({q.expected} {q.expectedScore:.3f} vs {other_.title if other_ else "?"} {other_.score if other_ else 0:.3f})'
            )
        md.append("")
        outside = [q for q in r.queries if not q.topK or not q.hybridTopK]
        if outside:
            md += [f"Expected section outside the top {top_k} (not in the prompt):", ""]
            for q in outside:
                rescue_note = (
                    f", vector + keyword rescue {'in' if q.rescueTopK else 'OUT'}"
                    if q.rescueEvaluated
                    else ""
                )
                md.append(
                    f'- [{q.company}, {q.style}] "{q.text}" → **{q.expected}**: vector {"in" if q.topK else "OUT"}, hybrid {"in" if q.hybridTopK else "OUT"}{rescue_note}'
                )
            md.append("")
        else:
            md += [f"Every expected section is within the top {top_k} for both rankings.", ""]
        differs = [q for q in r.queries if q.top1 != q.hybridTop1]
        if differs:
            md += [
                "Where hybrid ranking differs from vector-only (top-1):",
                "",
                *[
                    f'- [{q.company}] "{q.text}" → vector **{q.ranked[0].title}** ({"hit" if q.top1 else "miss"}), hybrid **{q.hybridRanked[0].title}** ({"hit" if q.hybridTop1 else "miss"})'
                    for q in differs
                ],
                "",
            ]
        else:
            md += ["Hybrid ranking agrees with vector-only on every top-1 result.", ""]
        md += [
            "Out-of-scope probes, best section score:",
            "",
            *[f'- {p.best.score:.3f} [{p.company}] "{p.text}" → {p.best.title}' for p in r.probes],
            "",
        ]

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "retrieval-results.json").write_text(
        json.dumps(
            {"model": model, "generatedAt": now, "results": [asdict(r) for r in results]}, indent=2
        )
    )
    (OUT / "retrieval-results.md").write_text("\n".join(md))
    print("wrote docs/evals/retrieval-results.{json,md}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
