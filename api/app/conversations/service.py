from __future__ import annotations

import base64
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Config
from app.db.models import Company, Conversation, Feedback, Message, User, utcnow
from app.deps import AppDeps
from app.errors import GuidelinesNotReadyError, NotFoundError
from app.lib import provider_error_message
from app.observability.tracer import (
    GenerationRecord,
    RetrievalOut,
    SummaryRecord,
    TurnEnd,
    TurnMeta,
    TurnRecorder,
)
from app.rag.guidance import GuidanceParseError, finalize_guidance
from app.rag.llm import ChatModelError
from app.rag.prompt import (
    SUMMARY_SYSTEM_PROMPT,
    HistoryTurn,
    LatestMessage,
    PromptInput,
    estimate_prompt_tokens,
    fit_history_to_budget,
    retrieval_query,
    transcript_for_summary,
)
from app.rag.retrieval import (
    merge_retrieved,
    retrieve_chunks_by_vector,
    retrieve_corrections,
    retrieve_keyword_rescue,
)
from app.schemas import (
    AssistantGuidance,
    Coverage,
    FeedbackSummary,
    MessageKind,
    MessageRole,
    MessageStatus,
    RetrievedChunk,
    UsedCorrection,
)
from app.schemas import Conversation as ConversationSchema
from app.schemas import ConversationSummary as ConversationSummarySchema
from app.schemas import Message as MessageSchema
from app.schemas import User as UserSchema

# Extra guideline sections admitted through a matching correction's original question.
CORRECTION_ANCHORED_SECTIONS = 2


def parse_uuid(value: str) -> UUID | None:
    try:
        return UUID(value)
    except ValueError:
        return None


def to_user(u: User) -> UserSchema:
    return UserSchema(id=str(u.id), username=u.username, displayName=u.display_name)


def encode_cursor(at: datetime, id: UUID) -> str:
    """Keyset cursor "timestamp|id", shared by the conversation list and message paging."""
    raw = f"{at.isoformat()}|{id}".encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, UUID] | None:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        ts, id_ = base64.urlsafe_b64decode(padded).decode().split("|", 1)
        return datetime.fromisoformat(ts), UUID(id_)
    except Exception:
        return None


@dataclass
class ListArgs:
    user_id: str
    company_id: str | None = None
    coverage: Coverage | None = None
    cursor: str | None = None
    limit: int | None = None


@dataclass
class ListResult:
    items: list[ConversationSummarySchema]
    next_cursor: str | None


@dataclass
class ConversationPage:
    conversation: ConversationSchema
    older_cursor: str | None


@dataclass
class SentMessages:
    user_message: MessageSchema
    assistant_message: MessageSchema


@dataclass
class _Loaded:
    conversation: Conversation
    company: Company
    message_count: int = 0


def compact_guidance(m: Message) -> str:
    """What an earlier assistant turn contributes to the next prompt: verdict + reply, not the
    whole JSON."""
    g = m.guidance
    if not g:
        return "(previous answer failed)" if m.status == MessageStatus.failed else m.content
    parts = [
        f"coverage: {g.get('coverage') or 'unknown'}",
        f"recommendedReply: {g.get('recommendedReply') or m.content}",
    ]
    if g.get("clarifications"):
        parts.append("clarifications: " + " | ".join(g["clarifications"]))
    return "\n".join(parts)


class ConversationsService:
    """Conversations are private to the agent who started them: every read is scoped by user."""

    def __init__(self, session: AsyncSession, deps: AppDeps) -> None:
        self._session = session
        self._deps = deps
        self._config: Config = deps.config
        # Users seen in this request; a conversation page names the same agent many times.
        self._users: dict[UUID, User] = {}

    async def _load_users(self, ids: list[UUID]) -> dict[UUID, User]:
        missing = [i for i in set(ids) if i not in self._users]
        if missing:
            rows = await self._session.scalars(select(User).where(User.id.in_(missing)))
            self._users.update({u.id: u for u in rows.all()})
        return self._users

    async def _summaries(
        self,
        rows: list[tuple[Conversation, str]],
        counts: dict[UUID, int] | None = None,
    ) -> list[ConversationSummarySchema]:
        if not rows:
            return []
        ids = [c.id for c, _ in rows]
        if counts is None:
            result = await self._session.execute(
                select(Message.conversation_id, func.count())
                .where(Message.conversation_id.in_(ids))
                .group_by(Message.conversation_id)
            )
            counts = dict(result.all())
        count_by = counts
        users = await self._load_users([c.created_by for c, _ in rows])
        return [
            ConversationSummarySchema(
                id=str(c.id),
                companyId=str(c.company_id),
                companyName=company_name,
                title=c.title,
                messageCount=count_by.get(c.id, 0),
                lastCoverage=c.last_coverage,
                createdBy=to_user(users[c.created_by]),
                createdAt=c.created_at,
                lastMessageAt=c.last_message_at,
            )
            for c, company_name in rows
        ]

    async def _load_conversation(self, conversation_id: str, user_id: str) -> _Loaded:
        """Loads a conversation the given agent owns, with its company, owner and message count
        in one query; another agent's conversation is a 404."""
        cid = parse_uuid(conversation_id)
        row = None
        if cid:
            count = (
                select(func.count())
                .where(Message.conversation_id == Conversation.id)
                .correlate(Conversation)
                .scalar_subquery()
            )
            row = (
                await self._session.execute(
                    select(Conversation, Company, User, count)
                    .join(Company, Company.id == Conversation.company_id)
                    .join(User, User.id == Conversation.created_by)
                    .where(Conversation.id == cid)
                )
            ).first()
        if row is None or str(row[0].created_by) != user_id:
            raise NotFoundError(
                "Conversation not found", resource="conversation", id=conversation_id
            )
        self._users[row[2].id] = row[2]
        return _Loaded(conversation=row[0], company=row[1], message_count=int(row[3]))

    async def map_messages(self, rows: list[Message]) -> list[MessageSchema]:
        if not rows:
            return []
        ids = [m.id for m in rows]
        feedback_rows = (
            await self._session.scalars(select(Feedback).where(Feedback.message_id.in_(ids)))
        ).all()
        users = await self._load_users(
            [m.created_by for m in rows] + [f.user_id for f in feedback_rows]
        )
        feedback_by: dict[UUID, list[FeedbackSummary]] = {}
        for f in feedback_rows:
            feedback_by.setdefault(f.message_id, []).append(
                FeedbackSummary(
                    id=str(f.id),
                    rating=f.rating,
                    whatWasWrong=f.what_was_wrong,
                    correctedAnswer=f.corrected_answer,
                    user=to_user(users[f.user_id]),
                    createdAt=f.created_at,
                )
            )
        return [
            MessageSchema(
                id=str(m.id),
                conversationId=str(m.conversation_id),
                role=m.role,
                content=m.content,
                status=m.status,
                error=m.error,
                guidance=AssistantGuidance.model_validate(m.guidance) if m.guidance else None,
                retrieval=[
                    RetrievedChunk(chunkId=r["chunkId"], title=r.get("title"), score=r["score"])
                    for r in m.retrieval
                ]
                if m.retrieval is not None
                else None,
                correctionsUsed=[
                    UsedCorrection(correctionId=c["correctionId"], score=c["score"])
                    for c in m.corrections_used
                ]
                if m.corrections_used is not None
                else None,
                guidelineVersionId=str(m.guideline_version_id) if m.guideline_version_id else None,
                model=m.model,
                promptTokens=m.prompt_tokens,
                completionTokens=m.completion_tokens,
                thinkingTokens=m.thinking_tokens,
                totalTokens=m.total_tokens,
                latencyMs=m.latency_ms,
                feedback=feedback_by.get(m.id),
                createdBy=to_user(users[m.created_by]),
                createdAt=m.created_at,
            )
            for m in rows
        ]

    async def _full(
        self,
        conversation_id: str,
        user_id: str,
        before: str | None = None,
        limit: int | None = None,
    ) -> ConversationPage:
        """The conversation with one page of messages: the newest `limit` (default 50), or the
        `limit` before `before`. Messages are returned in chronological order; `older_cursor`
        points at the page's first message when older ones exist."""
        loaded = await self._load_conversation(conversation_id, user_id)
        conv = loaded.conversation
        summary = (
            await self._summaries(
                [(conv, loaded.company.name)], counts={conv.id: loaded.message_count}
            )
        )[0]
        page_size = min(max(limit or 50, 1), 100)
        cursor = decode_cursor(before) if before else None
        stmt = select(Message).where(Message.conversation_id == conv.id)
        if cursor:
            at, mid = cursor
            stmt = stmt.where(
                or_(Message.created_at < at, and_(Message.created_at == at, Message.id < mid))
            )
        rows = list(
            (
                await self._session.scalars(
                    stmt.order_by(Message.created_at.desc(), Message.id.desc()).limit(page_size + 1)
                )
            ).all()
        )
        page = list(reversed(rows[:page_size]))
        oldest = page[0] if page else None
        return ConversationPage(
            conversation=ConversationSchema(
                summary=summary, messages=await self.map_messages(page)
            ),
            older_cursor=encode_cursor(oldest.created_at, oldest.id)
            if len(rows) > page_size and oldest
            else None,
        )

    async def create(self, company_id: str, user_id: str) -> ConversationSchema:
        cid = parse_uuid(company_id)
        company = await self._session.get(Company, cid) if cid else None
        if company is None:
            raise NotFoundError("Company not found", resource="company", id=company_id)
        if not company.active_guideline_version_id:
            raise GuidelinesNotReadyError(
                "This company has no processed guidelines yet. Upload guidelines before starting a chat.",
                company_id=company_id,
            )
        row = Conversation(company_id=company.id, created_by=UUID(user_id))
        self._session.add(row)
        await self._session.commit()
        return (await self._full(str(row.id), user_id)).conversation

    async def list(self, args: ListArgs) -> ListResult:
        page_size = min(max(args.limit or 20, 1), 100)
        stmt = (
            select(Conversation, Company.name)
            .join(Company, Company.id == Conversation.company_id)
            .where(Conversation.created_by == UUID(args.user_id))
        )
        if args.company_id:
            cid = parse_uuid(args.company_id)
            if cid is None:
                return ListResult(items=[], next_cursor=None)
            stmt = stmt.where(Conversation.company_id == cid)
        if args.coverage:
            stmt = stmt.where(Conversation.last_coverage == args.coverage)
        cursor = decode_cursor(args.cursor) if args.cursor else None
        if cursor:
            at, cid_ = cursor
            stmt = stmt.where(
                or_(
                    Conversation.last_message_at < at,
                    and_(Conversation.last_message_at == at, Conversation.id < cid_),
                )
            )
        rows = (
            await self._session.execute(
                stmt.order_by(Conversation.last_message_at.desc(), Conversation.id.desc()).limit(
                    page_size + 1
                )
            )
        ).all()
        page = [(c, name) for c, name in rows[:page_size]]
        items = await self._summaries(page)
        last = page[-1][0] if page else None
        return ListResult(
            items=items,
            next_cursor=encode_cursor(last.last_message_at, last.id)
            if len(rows) > page_size and last
            else None,
        )

    async def get(
        self,
        conversation_id: str,
        user_id: str,
        *,
        before: str | None = None,
        limit: int | None = None,
    ) -> ConversationPage:
        return await self._full(conversation_id, user_id, before, limit)

    async def send_message(
        self, *, conversation_id: str, kind: MessageKind, content: str, user_id: str
    ) -> SentMessages:
        session = self._session
        config = self._config
        deps = self._deps
        loaded = await self._load_conversation(conversation_id, user_id)
        conversation, company = loaded.conversation, loaded.company
        if not company.active_guideline_version_id:
            raise GuidelinesNotReadyError(
                "The company has no active guidelines", company_id=str(company.id)
            )
        version_id = company.active_guideline_version_id
        text = content.strip()
        role = MessageRole(kind.value)

        history = list(
            (
                await session.scalars(
                    select(Message)
                    .where(Message.conversation_id == conversation.id)
                    .order_by(Message.created_at.asc(), Message.id.asc())
                )
            ).all()
        )

        # Idempotent retry: re-sending the same text right after a failed assistant turn reuses
        # the user message.
        last_msg = history[-1] if history else None
        prev_user = history[-2] if len(history) >= 2 else None
        if (
            last_msg is not None
            and last_msg.role == MessageRole.assistant
            and last_msg.status == MessageStatus.failed
            and prev_user is not None
            and prev_user.role != MessageRole.assistant
            and prev_user.content == text
            and prev_user.role == role
        ):
            await session.execute(delete(Message).where(Message.id == last_msg.id))
            await session.commit()
            user_message = prev_user
            prior_history = history[:-2]
        else:
            user_message = Message(
                conversation_id=conversation.id,
                role=role,
                content=text,
                status=MessageStatus.ok,
                created_by=UUID(user_id),
            )
            session.add(user_message)
            if not conversation.title and kind == MessageKind.customer:
                conversation.title = text[:77] + "…" if len(text) > 80 else text
            await session.commit()
            prior_history = history

        # Messages already folded into the rolling summary are not replayed verbatim.
        summarised_upto = 0
        if conversation.history_summary_upto:
            idx = next(
                (
                    i
                    for i, m in enumerate(prior_history)
                    if m.id == conversation.history_summary_upto
                ),
                -1,
            )
            summarised_upto = idx + 1
        unsummarised = prior_history[summarised_upto:]
        window = unsummarised[-config.CHAT_HISTORY_WINDOW :]
        overflow = unsummarised[: len(unsummarised) - len(window)]

        def to_turn(m: Message) -> HistoryTurn:
            # Older assistant turns are compacted to what matters for continuity, not the full JSON.
            return HistoryTurn(
                role=m.role.value,
                content=compact_guidance(m) if m.role == MessageRole.assistant else m.content,
            )

        history_turns = [to_turn(m) for m in window]
        latest = LatestMessage(kind=kind.value, content=text)
        query = retrieval_query(history_turns, latest)
        chat_model = deps.chat_model
        embedder = deps.embedder
        log = deps.log

        async def turn_body(turn: TurnRecorder) -> Message:
            started = time.monotonic()
            # Rolling summary: fold turns that fell out of the window into one short paragraph
            # so very long chats keep their context without growing the prompt.
            summary = conversation.history_summary
            if overflow:
                summary_started = time.monotonic()
                inp = transcript_for_summary(summary, [to_turn(m) for m in overflow])
                try:
                    output = await chat_model.summarize(SUMMARY_SYSTEM_PROMPT, inp)
                    if output:
                        summary = output
                        conversation.history_summary = output
                        conversation.history_summary_upto = overflow[-1].id
                        await session.commit()
                    latency = int((time.monotonic() - summary_started) * 1000)
                    turn.summary(
                        SummaryRecord(
                            model=chat_model.model,
                            messages=len(overflow),
                            input=inp,
                            output=output,
                            latencyMs=latency,
                        )
                    )
                    log.info(
                        "history summarised",
                        conversationId=str(conversation.id),
                        messages=len(overflow),
                        latencyMs=latency,
                    )
                except Exception as err:
                    # Not fatal: answer with the window only; the overflow is retried next turn.
                    message = err.message if isinstance(err, ChatModelError) else "summary failed"
                    turn.summary(
                        SummaryRecord(
                            model=chat_model.model,
                            messages=len(overflow),
                            input=inp,
                            error=message,
                            latencyMs=int((time.monotonic() - summary_started) * 1000),
                        )
                    )
                    log.warning(
                        "history summary failed; continuing without it",
                        err=str(err),
                        conversationId=str(conversation.id),
                    )

            base: dict[str, Any] = {
                "conversation_id": conversation.id,
                "role": MessageRole.assistant,
                "created_by": UUID(user_id),
                "guideline_version_id": version_id,
                "model": chat_model.model,
                "trace_id": turn.trace_id,
            }

            # Retrieval and prompt assembly. A provider failure here (embedding the message) is
            # stored as a failed turn exactly like a generation failure, so the agent's message
            # is never left without an assistant row and a retry reuses it.
            retrieval_started = time.monotonic()
            try:
                query_vector = await embedder.embed_query(query)
                direct = await retrieve_chunks_by_vector(
                    session,
                    version_id=version_id,
                    vector=query_vector,
                    top_k=config.RAG_TOP_K,
                    min_score=config.RAG_MIN_SCORE,
                )
                corrections = await retrieve_corrections(
                    session,
                    embedder,
                    company_id=company.id,
                    query=query,
                    top_k=config.RAG_CORRECTIONS_TOP_K,
                    min_score=config.RAG_CORRECTIONS_MIN_SCORE,
                )
                # Correction-anchored retrieval: reuse the best correction's stored question
                # embedding, no extra provider call.
                anchor = corrections[0].queryEmbedding if corrections else None
                anchored = (
                    merge_retrieved(
                        direct,
                        await retrieve_chunks_by_vector(
                            session,
                            version_id=version_id,
                            vector=anchor,
                            top_k=config.RAG_TOP_K,
                            min_score=config.RAG_MIN_SCORE,
                        ),
                        CORRECTION_ANCHORED_SECTIONS,
                    )
                    if anchor
                    else direct
                )
                # Keyword rescue: a section the vector ranking missed but that a distinctive word
                # of the message points at is appended, never reordered.
                rescued = await retrieve_keyword_rescue(
                    session,
                    version_id=version_id,
                    query=query,
                    vector=query_vector,
                    exclude=[s.chunkId for s in anchored],
                )
                sections = [*anchored, rescued] if rescued else anchored
                turn.retrieval(query, RetrievalOut(sections=sections, corrections=corrections))
                prompt, dropped = fit_history_to_budget(
                    PromptInput(
                        companyName=company.name,
                        summary=summary,
                        sections=sections,
                        corrections=corrections,
                        history=history_turns,
                        latest=latest,
                    ),
                    config.CHAT_PROMPT_TOKEN_BUDGET,
                )
            except Exception as err:
                latency = int((time.monotonic() - retrieval_started) * 1000)
                message = (
                    provider_error_message(err) or "The assistant could not look up the guidelines"
                )
                log.error("retrieval failed", err=str(err), conversationId=str(conversation.id))
                row = Message(
                    **base,
                    retrieval=[],
                    corrections_used=[],
                    content="",
                    status=MessageStatus.failed,
                    error=message,
                    latency_ms=latency,
                )
                session.add(row)
                await session.commit()
                turn.end(TurnEnd(status="failed", messageId=str(row.id)))
                return row

            estimated = estimate_prompt_tokens(prompt)
            base["retrieval"] = [
                {
                    "chunkId": s.chunkId,
                    "title": s.title,
                    "score": s.score,
                    **({"via": s.via} if s.via else {}),
                }
                for s in sections
            ]
            base["corrections_used"] = [
                {"correctionId": c.correctionId, "score": c.score} for c in corrections
            ]

            def record(latency_ms: int, **g: Any) -> None:
                used = g.get("promptTokens") or estimated
                pct = round(used / config.GEMINI_CONTEXT_WINDOW_TOKENS * 10000) / 100
                turn.generation(
                    GenerationRecord(
                        model=chat_model.model,
                        system=prompt.system,
                        turns=prompt.turns,
                        estimatedPromptTokens=estimated,
                        contextWindowTokens=config.GEMINI_CONTEXT_WINDOW_TOKENS,
                        contextUsedPct=pct,
                        droppedHistoryTurns=dropped,
                        latencyMs=latency_ms,
                        **g,
                    )
                )
                log.info(
                    "llm call failed" if g.get("error") else "llm call",
                    conversationId=str(conversation.id),
                    model=chat_model.model,
                    promptTokens=g.get("promptTokens"),
                    completionTokens=g.get("completionTokens"),
                    thinkingTokens=g.get("thinkingTokens"),
                    totalTokens=g.get("totalTokens"),
                    finishReason=g.get("finishReason"),
                    estimatedPromptTokens=estimated,
                    contextWindowTokens=config.GEMINI_CONTEXT_WINDOW_TOKENS,
                    contextUsedPct=pct,
                    droppedHistoryTurns=dropped,
                    latencyMs=latency_ms,
                    sections=len(sections),
                    corrections=len(corrections),
                    **({"error": g["error"]} if g.get("error") else {}),
                )

            try:
                result = await chat_model.generate_guidance(prompt.system, prompt.turns)
                latency = int((time.monotonic() - started) * 1000)
                record(
                    latency,
                    raw=result.raw,
                    promptTokens=result.promptTokens,
                    completionTokens=result.completionTokens,
                    thinkingTokens=result.thinkingTokens,
                    totalTokens=result.totalTokens,
                    finishReason=result.finishReason,
                )
                guidance = finalize_guidance(result.raw, prompt.sectionIds)
                row = Message(
                    **base,
                    content=guidance.recommendedReply or "",
                    status=MessageStatus.ok,
                    guidance=guidance.model_dump(mode="json", exclude_none=True),
                    coverage=guidance.coverage or Coverage.partial,
                    prompt_tokens=result.promptTokens,
                    completion_tokens=result.completionTokens,
                    thinking_tokens=result.thinkingTokens,
                    total_tokens=result.totalTokens,
                    latency_ms=latency,
                )
                session.add(row)
                await session.commit()
                turn.end(
                    TurnEnd(status="ok", coverage=guidance.coverage.value, messageId=str(row.id))
                )
                return row
            except Exception as err:
                latency = int((time.monotonic() - started) * 1000)
                known = isinstance(err, ChatModelError | GuidanceParseError)
                message = str(err) if known else "The assistant could not produce a response"
                if not known:
                    log.error(
                        "unexpected error while generating guidance",
                        err=str(err),
                        conversationId=str(conversation.id),
                    )
                record(latency, error=message)
                row = Message(
                    **base,
                    content="",
                    status=MessageStatus.failed,
                    error=message,
                    latency_ms=latency,
                )
                session.add(row)
                await session.commit()
                turn.end(TurnEnd(status="failed", messageId=str(row.id)))
                return row

        assistant = await deps.tracer.run_turn(
            TurnMeta(
                conversationId=str(conversation.id),
                userId=user_id,
                companyId=str(company.id),
                companyName=company.name,
                guidelineVersionId=str(version_id),
                kind=kind.value,
                content=text,
            ),
            turn_body,
        )

        # A failed turn has no coverage; the previous verdict stays until the retry succeeds.
        values: dict[str, Any] = {"last_message_at": assistant.created_at, "updated_at": utcnow()}
        if assistant.coverage:
            values["last_coverage"] = assistant.coverage
        await session.execute(
            update(Conversation).where(Conversation.id == conversation.id).values(**values)
        )
        await session.commit()

        u, a = await self.map_messages([user_message, assistant])
        return SentMessages(user_message=u, assistant_message=a)
