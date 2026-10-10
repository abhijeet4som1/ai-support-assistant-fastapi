"""Guideline version rows → API summaries, with their uploader."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import GuidelineVersion, User
from app.schemas import GuidelineVersionSummary
from app.schemas import User as UserSchema


@dataclass
class VersionWithUploader:
    version: GuidelineVersion
    uploader: User


def to_user(u: User) -> UserSchema:
    return UserSchema(id=str(u.id), username=u.username, displayName=u.display_name)


def to_version_summary(
    v: VersionWithUploader, active_version_id: UUID | None
) -> GuidelineVersionSummary:
    row = v.version
    return GuidelineVersionSummary(
        id=str(row.id),
        companyId=str(row.company_id),
        filename=row.filename,
        contentType=row.content_type,
        sizeBytes=row.size_bytes,
        status=row.status,
        chunksTotal=row.chunks_total,
        chunksEmbedded=row.chunks_embedded,
        error=row.error,
        isActive=row.id == active_version_id,
        uploadedBy=to_user(v.uploader),
        createdAt=row.created_at,
        updatedAt=row.updated_at,
        readyAt=row.ready_at,
        supersededBy=str(row.superseded_by) if row.superseded_by else None,
    )


def _with_uploader():  # type: ignore[no-untyped-def]
    return select(GuidelineVersion, User).join(User, User.id == GuidelineVersion.created_by)


async def load_versions_by_id(
    session: AsyncSession, ids: list[UUID]
) -> dict[UUID, VersionWithUploader]:
    """Loads versions by id together with their uploader."""
    if not ids:
        return {}
    rows = await session.execute(_with_uploader().where(GuidelineVersion.id.in_(ids)))
    return {v.id: VersionWithUploader(v, u) for v, u in rows.all()}


async def load_latest_versions_by_company(
    session: AsyncSession, company_ids: list[UUID]
) -> dict[UUID, VersionWithUploader]:
    """Latest version (highest seq) per company, keyed by company id."""
    if not company_ids:
        return {}
    latest = (
        select(
            GuidelineVersion.company_id.label("company_id"),
            func.max(GuidelineVersion.seq).label("max_seq"),
        )
        .where(GuidelineVersion.company_id.in_(company_ids))
        .group_by(GuidelineVersion.company_id)
        .subquery("latest")
    )
    rows = await session.execute(
        select(GuidelineVersion, User)
        .join(latest, latest.c.max_seq == GuidelineVersion.seq)
        .join(User, User.id == GuidelineVersion.created_by)
        .order_by(GuidelineVersion.seq.desc())
    )
    return {v.company_id: VersionWithUploader(v, u) for v, u in rows.all()}


async def load_versions_for_company(
    session: AsyncSession, company_id: UUID
) -> list[VersionWithUploader]:
    rows = await session.execute(
        _with_uploader()
        .where(GuidelineVersion.company_id == company_id)
        .order_by(GuidelineVersion.seq.desc())
    )
    return [VersionWithUploader(v, u) for v, u in rows.all()]
