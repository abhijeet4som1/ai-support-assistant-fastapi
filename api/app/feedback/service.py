from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Company, Conversation, Feedback, Message, User, utcnow
from app.deps import AppDeps
from app.errors import ConflictError, NotFoundError, ValidationException
from app.observability.tracer import ScoreInput
from app.schemas import Correction, FeedbackRating, MessageRole, MessageStatus
from app.schemas import User as UserSchema


def parse_uuid(value: str) -> UUID | None:
    try:
        return UUID(value)
    except ValueError:
        return None


@dataclass
class SubmitFeedbackInput:
    message_id: str
    rating: FeedbackRating
    user_id: str
    what_was_wrong: str | None = None
    corrected_answer: str | None = None


class FeedbackService:
    def __init__(self, session: AsyncSession, deps: AppDeps) -> None:
        self._session = session
        self._deps = deps

    async def _to_corrections(self, rows: list[Feedback]) -> list[Correction]:
        if not rows:
            return []
        users = (
            await self._session.scalars(
                select(User).where(User.id.in_(list({r.user_id for r in rows})))
            )
        ).all()
        by_id = {u.id: u for u in users}
        out: list[Correction] = []
        for f in rows:
            u = by_id[f.user_id]
            out.append(
                Correction(
                    id=str(f.id),
                    companyId=str(f.company_id),
                    conversationId=str(f.conversation_id),
                    messageId=str(f.message_id),
                    rating=f.rating,
                    queryText=f.query_text,
                    whatWasWrong=f.what_was_wrong,
                    correctedAnswer=f.corrected_answer,
                    guidelineVersionId=str(f.guideline_version_id),
                    active=f.active,
                    user=UserSchema(id=str(u.id), username=u.username, displayName=u.display_name),
                    createdAt=f.created_at,
                )
            )
        return out

    async def _one(self, correction_id: str) -> Correction:
        cid = parse_uuid(correction_id)
        row = await self._session.get(Feedback, cid) if cid else None
        if row is None:
            raise NotFoundError("Correction not found", resource="correction", id=correction_id)
        return (await self._to_corrections([row]))[0]

    async def submit(self, inp: SubmitFeedbackInput) -> Correction:
        session = self._session
        mid = parse_uuid(inp.message_id)
        message = await session.get(Message, mid) if mid else None
        if message is None:
            raise NotFoundError("Message not found", resource="message", id=inp.message_id)
        if message.role != MessageRole.assistant or message.status != MessageStatus.ok:
            raise ConflictError("Only successful assistant answers can be rated")
        what_was_wrong = (inp.what_was_wrong or "").strip() or None
        corrected_answer = (inp.corrected_answer or "").strip() or None
        if inp.rating == FeedbackRating.down and not corrected_answer:
            raise ValidationException(
                "A corrected answer is required when rating an answer down",
                field_list=[
                    {
                        "path": "/correctedAnswer",
                        "message": "Provide the answer the assistant should have given",
                    }
                ],
            )

        conversation = await session.get(Conversation, message.conversation_id)
        # Conversations are private: an answer in another agent's thread cannot be rated.
        if conversation is None or str(conversation.created_by) != inp.user_id:
            raise NotFoundError(
                "Conversation not found", resource="conversation", id=str(message.conversation_id)
            )

        # The customer message this answer responded to: last customer turn before the answer.
        customer = await session.scalar(
            select(Message)
            .where(
                Message.conversation_id == message.conversation_id,
                Message.role == MessageRole.customer,
                Message.created_at < message.created_at,
            )
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        query_text = customer.content if customer else message.content

        guideline_version_id = message.guideline_version_id
        if not guideline_version_id:
            company = await session.get(Company, conversation.company_id)
            guideline_version_id = company.active_guideline_version_id if company else None
        if not guideline_version_id:
            raise ConflictError("Cannot store feedback: no guideline version is associated")

        query_embedding = await self._deps.embedder.embed_query(query_text)
        values = {
            "message_id": message.id,
            "conversation_id": message.conversation_id,
            "company_id": conversation.company_id,
            "user_id": UUID(inp.user_id),
            "rating": inp.rating,
            "what_was_wrong": what_was_wrong,
            "corrected_answer": corrected_answer,
            "query_text": query_text,
            "query_embedding": query_embedding,
            "guideline_version_id": guideline_version_id,
            "active": True,
        }
        stmt = insert(Feedback).values(**values, created_at=utcnow(), updated_at=utcnow())
        upsert = stmt.on_conflict_do_update(
            index_elements=[Feedback.message_id, Feedback.user_id],
            set_={
                "rating": stmt.excluded.rating,
                "what_was_wrong": stmt.excluded.what_was_wrong,
                "corrected_answer": stmt.excluded.corrected_answer,
                "query_text": stmt.excluded.query_text,
                "query_embedding": stmt.excluded.query_embedding,
                "guideline_version_id": stmt.excluded.guideline_version_id,
                "active": True,
                "updated_at": utcnow(),
            },
        ).returning(Feedback.id)
        feedback_id = await session.scalar(upsert)
        await session.commit()
        row = await session.get(Feedback, feedback_id)
        assert row is not None
        session.expire(row)
        row = await session.get(Feedback, feedback_id)
        assert row is not None

        # Attach the agent's verdict to the trace of the turn that produced the answer.
        if message.trace_id:
            tracer = self._deps.tracer
            tracer.score(
                ScoreInput(
                    traceId=message.trace_id,
                    name="agent-rating",
                    value=1 if inp.rating == FeedbackRating.up else 0,
                    dataType="BOOLEAN",
                    comment=what_was_wrong,
                    metadata={"messageId": str(message.id), "feedbackId": str(row.id)},
                )
            )
            if corrected_answer:
                tracer.score(
                    ScoreInput(
                        traceId=message.trace_id,
                        name="agent-correction",
                        value=corrected_answer[:499] + "…"
                        if len(corrected_answer) > 500
                        else corrected_answer,
                        dataType="TEXT",
                        metadata={"messageId": str(message.id), "feedbackId": str(row.id)},
                    )
                )
        return (await self._to_corrections([row]))[0]

    async def list_corrections(self, company_id: str, include_inactive: bool) -> list[Correction]:
        cid = parse_uuid(company_id)
        company = await self._session.get(Company, cid) if cid else None
        if company is None:
            raise NotFoundError("Company not found", resource="company", id=company_id)
        stmt = select(Feedback).where(Feedback.company_id == company.id)
        if not include_inactive:
            stmt = stmt.where(Feedback.active.is_(True))
        rows = (
            await self._session.scalars(
                stmt.order_by(Feedback.created_at.desc(), Feedback.id.asc())
            )
        ).all()
        return await self._to_corrections(list(rows))

    async def update_correction(self, correction_id: str, active: bool) -> Correction:
        await self._one(correction_id)
        row = await self._session.get(Feedback, UUID(correction_id))
        assert row is not None
        row.active = active
        await self._session.commit()
        return await self._one(correction_id)
