from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Company, Feedback, GuidelineChunk, GuidelineVersion, User, utcnow
from app.db.session import transaction
from app.errors import (
    ConflictError,
    GuidelinesConflictError,
    GuidelinesNotReadyError,
    NotFoundError,
    PayloadTooLargeError,
)
from app.guidelines.mappers import (
    load_versions_by_id,
    load_versions_for_company,
    to_version_summary,
)
from app.ingestion.parsers import detect_file_kind
from app.jobs.queue import INGEST_GUIDELINES, JobQueue
from app.schemas import GuidelineChunk as GuidelineChunkSchema
from app.schemas import GuidelineStatus, GuidelineVersionSummary

IN_FLIGHT = [
    GuidelineStatus.queued,
    GuidelineStatus.parsing,
    GuidelineStatus.chunking,
    GuidelineStatus.embedding,
]


def parse_uuid(value: str) -> UUID | None:
    try:
        return UUID(value)
    except ValueError:
        return None


@dataclass
class UploadInput:
    company_id: str
    filename: str
    body: bytes
    user_id: str
    file_content_type: str | None = None
    expected_version_id: str | None = None


@dataclass
class UploadResult:
    version: GuidelineVersionSummary
    created: bool


@dataclass
class ActiveGuidelines:
    version: GuidelineVersionSummary
    text: str
    chunks: list[GuidelineChunkSchema]


class GuidelinesService:
    def __init__(self, session: AsyncSession, queue: JobQueue, *, max_upload_bytes: int) -> None:
        self._session = session
        self._queue = queue
        self._max = max_upload_bytes

    async def _require_company(self, company_id: str, *, for_update: bool = False) -> Company:
        uid = parse_uuid(company_id)
        company = None
        if uid:
            stmt = select(Company).where(Company.id == uid)
            if for_update:
                stmt = stmt.with_for_update()
            company = await self._session.scalar(stmt)
        if company is None:
            raise NotFoundError("Company not found", resource="company", id=company_id)
        return company

    async def _require_version(self, version_id: str) -> GuidelineVersion:
        uid = parse_uuid(version_id)
        v = await self._session.get(GuidelineVersion, uid) if uid else None
        if v is None:
            raise NotFoundError(
                "Guideline version not found", resource="guidelineVersion", id=version_id
            )
        return v

    async def summary(self, version_id: str | UUID) -> GuidelineVersionSummary:
        uid = version_id if isinstance(version_id, UUID) else parse_uuid(version_id)
        self._session.expire_all()
        v = (await load_versions_by_id(self._session, [uid])).get(uid) if uid else None
        if v is None:
            raise NotFoundError(
                "Guideline version not found", resource="guidelineVersion", id=str(version_id)
            )
        company = await self._require_company(str(v.version.company_id))
        return to_version_summary(v, company.active_guideline_version_id)

    async def upload(self, inp: UploadInput) -> UploadResult:
        if len(inp.body) > self._max:
            raise PayloadTooLargeError(
                f"File is larger than the {round(self._max / 1024 / 1024)} MB limit",
                max_bytes=self._max,
            )
        if len(inp.body) == 0:
            raise PayloadTooLargeError("The uploaded file is empty", max_bytes=self._max)
        detected = detect_file_kind(inp.filename, inp.body, inp.file_content_type)
        sha256 = hashlib.sha256(inp.body).hexdigest()

        async with transaction(self._session):
            # Serialise uploads per company so two agents cannot race on "latest".
            company = await self._require_company(inp.company_id, for_update=True)
            latest = await self._session.scalar(
                select(GuidelineVersion)
                .where(GuidelineVersion.company_id == company.id)
                .order_by(GuidelineVersion.seq.desc())
                .limit(1)
            )
            if inp.expected_version_id and latest and str(latest.id) != inp.expected_version_id:
                uploader = await self._session.get(User, latest.created_by)
                name = uploader.display_name if uploader else "Another user"
                raise GuidelinesConflictError(
                    f"{name} uploaded new guidelines after you opened this page",
                    latest_version_id=str(latest.id),
                    uploaded_by={
                        "id": str(uploader.id),
                        "username": uploader.username,
                        "displayName": uploader.display_name,
                    }
                    if uploader
                    else {"id": "", "username": "", "displayName": "Another user"},
                    uploaded_at=latest.created_at,
                )

            # Same file as the active version: nothing to do.
            if (
                company.active_guideline_version_id
                and latest is not None
                and latest.id == company.active_guideline_version_id
                and latest.sha256 == sha256
            ):
                version_id = latest.id
                created = False
            else:
                await self._session.execute(
                    update(GuidelineVersion)
                    .where(
                        GuidelineVersion.company_id == company.id,
                        GuidelineVersion.status.in_(IN_FLIGHT),
                    )
                    .values(status=GuidelineStatus.superseded, updated_at=utcnow())
                )
                version = GuidelineVersion(
                    company_id=company.id,
                    filename=inp.filename,
                    content_type=detected.content_type,
                    size_bytes=len(inp.body),
                    sha256=sha256,
                    file_bytes=inp.body,
                    status=GuidelineStatus.queued,
                    created_by=UUID(inp.user_id),
                )
                self._session.add(version)
                await self._session.flush()
                # Point superseded versions at their successor (informational).
                await self._session.execute(
                    update(GuidelineVersion)
                    .where(
                        GuidelineVersion.company_id == company.id,
                        GuidelineVersion.status == GuidelineStatus.superseded,
                        GuidelineVersion.superseded_by.is_(None),
                    )
                    .values(superseded_by=version.id)
                )
                version_id = version.id
                created = True
        await self._session.commit()

        if created:
            job_id = await self._queue.enqueue(
                INGEST_GUIDELINES, {"versionId": str(version_id)}, singleton_key=str(version_id)
            )
            if job_id:
                await self._session.execute(
                    update(GuidelineVersion)
                    .where(GuidelineVersion.id == version_id)
                    .values(job_id=job_id)
                )
                await self._session.commit()
        return UploadResult(await self.summary(version_id), created)

    async def get_active(self, company_id: str) -> ActiveGuidelines:
        company = await self._require_company(company_id)
        if not company.active_guideline_version_id:
            latest_status = await self._session.scalar(
                select(GuidelineVersion.status)
                .where(GuidelineVersion.company_id == company.id)
                .order_by(GuidelineVersion.seq.desc())
                .limit(1)
            )
            raise GuidelinesNotReadyError(
                "Guidelines are still being processed"
                if latest_status
                else "No guidelines have been uploaded for this company yet",
                company_id=company_id,
                latest_status=latest_status.value if latest_status else None,
            )
        active_id = company.active_guideline_version_id
        v = (await load_versions_by_id(self._session, [active_id]))[active_id]
        chunks = (
            await self._session.scalars(
                select(GuidelineChunk)
                .where(GuidelineChunk.version_id == active_id)
                .order_by(GuidelineChunk.ordinal.asc())
            )
        ).all()
        return ActiveGuidelines(
            version=to_version_summary(v, active_id),
            text=v.version.raw_text or "",
            chunks=[
                GuidelineChunkSchema(
                    id=str(c.id),
                    ordinal=c.ordinal,
                    title=c.title,
                    content=c.content,
                    tokenCount=c.token_count,
                )
                for c in chunks
            ],
        )

    async def list_versions(self, company_id: str) -> list[GuidelineVersionSummary]:
        company = await self._require_company(company_id)
        versions = await load_versions_for_company(self._session, company.id)
        return [to_version_summary(v, company.active_guideline_version_id) for v in versions]

    async def get_version(self, version_id: str) -> GuidelineVersionSummary:
        return await self.summary(version_id)

    async def retry(self, version_id: str) -> GuidelineVersionSummary:
        v = await self._require_version(version_id)
        if v.status != GuidelineStatus.failed:
            raise ConflictError(
                f'Only failed versions can be retried (status is "{v.status.value}")'
            )
        v.status = GuidelineStatus.queued
        v.error = None
        v.chunks_embedded = 0
        await self._session.commit()
        job_id = await self._queue.enqueue(
            INGEST_GUIDELINES,
            {"versionId": str(v.id)},
            singleton_key=f"{v.id}:{int(time.time() * 1000)}",
        )
        if job_id:
            v.job_id = job_id
            await self._session.commit()
        return await self.summary(v.id)

    async def activate(self, version_id: str) -> GuidelineVersionSummary:
        v = await self._require_version(version_id)
        if v.status != GuidelineStatus.ready:
            raise ConflictError(
                f'Only ready versions can be activated (status is "{v.status.value}")'
            )
        await set_active_version(self._session, v.company_id, v.id, force=True)
        return await self.summary(v.id)


async def set_active_version(
    session: AsyncSession, company_id: UUID, version_id: UUID, *, force: bool
) -> None:
    """Makes `version_id` the active version of its company and deactivates corrections written
    against other versions. With `force=False` an older version never overwrites a newer active
    one (a slow job finishing late)."""
    async with transaction(session):
        company = await session.scalar(
            select(Company).where(Company.id == company_id).with_for_update()
        )
        if company is None:
            return
        if not force and company.active_guideline_version_id:
            current = await session.scalar(
                select(GuidelineVersion.seq).where(
                    GuidelineVersion.id == company.active_guideline_version_id
                )
            )
            nxt = await session.scalar(
                select(GuidelineVersion.seq).where(GuidelineVersion.id == version_id)
            )
            if current is not None and nxt is not None and nxt < current:
                return
        await session.execute(
            update(Company)
            .where(Company.id == company_id)
            .values(active_guideline_version_id=version_id, updated_at=utcnow())
        )
        await session.execute(
            update(Feedback)
            .where(
                Feedback.company_id == company_id,
                Feedback.guideline_version_id != version_id,
                Feedback.active.is_(True),
            )
            .values(active=False, updated_at=utcnow())
        )
    await session.commit()
