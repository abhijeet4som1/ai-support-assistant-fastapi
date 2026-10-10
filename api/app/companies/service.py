from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Company, Conversation
from app.db.session import is_unique_violation
from app.errors import ConflictError, NotFoundError
from app.guidelines.mappers import (
    load_latest_versions_by_company,
    load_versions_by_id,
    to_version_summary,
)
from app.schemas import Company as CompanySchema


def parse_uuid(value: str) -> UUID | None:
    try:
        return UUID(value)
    except ValueError:
        return None


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip())


def blank_to_none(value: str | None) -> str | None:
    trimmed = value.strip() if value else ""
    return trimmed or None


class CompaniesService:
    """Company data is shared; `conversationCount` is the calling agent's own count, since
    conversations are private."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def hydrate(self, rows: list[Company], user_id: str) -> list[CompanySchema]:
        if not rows:
            return []
        ids = [r.id for r in rows]
        active_ids = [r.active_guideline_version_id for r in rows if r.active_guideline_version_id]
        active = await load_versions_by_id(self._session, active_ids)
        latest = await load_latest_versions_by_company(self._session, ids)
        counts = await self._session.execute(
            select(Conversation.company_id, func.count())
            .where(Conversation.company_id.in_(ids), Conversation.created_by == UUID(user_id))
            .group_by(Conversation.company_id)
        )
        count_by = {company_id: n for company_id, n in counts.all()}
        out: list[CompanySchema] = []
        for r in rows:
            active_v = (
                active.get(r.active_guideline_version_id) if r.active_guideline_version_id else None
            )
            latest_v = latest.get(r.id)
            out.append(
                CompanySchema(
                    id=str(r.id),
                    name=r.name,
                    description=r.description,
                    activeGuidelines=to_version_summary(active_v, r.active_guideline_version_id)
                    if active_v
                    else None,
                    latestGuidelines=to_version_summary(latest_v, r.active_guideline_version_id)
                    if latest_v
                    else None,
                    conversationCount=count_by.get(r.id, 0),
                    createdAt=r.created_at,
                    updatedAt=r.updated_at,
                )
            )
        return out

    async def get_row(self, company_id: str) -> Company:
        uid = parse_uuid(company_id)
        row = await self._session.get(Company, uid) if uid else None
        if row is None:
            raise NotFoundError("Company not found", resource="company", id=company_id)
        return row

    async def list(self, user_id: str) -> list[CompanySchema]:
        rows = (await self._session.scalars(select(Company).order_by(Company.name.asc()))).all()
        return await self.hydrate(list(rows), user_id)

    async def get(self, company_id: str, user_id: str) -> CompanySchema:
        return (await self.hydrate([await self.get_row(company_id)], user_id))[0]

    async def create(self, *, name: str, description: str | None, created_by: str) -> CompanySchema:
        normalized = normalize_name(name)
        row = Company(
            name=normalized, description=blank_to_none(description), created_by=UUID(created_by)
        )
        self._session.add(row)
        try:
            await self._session.commit()
        except IntegrityError as err:
            await self._session.rollback()
            if is_unique_violation(err):
                raise ConflictError(f'A company named "{normalized}" already exists') from None
            raise
        return (await self.hydrate([row], created_by))[0]

    async def update(
        self, company_id: str, *, name: str | None, description: str | None, user_id: str
    ) -> CompanySchema:
        row = await self.get_row(company_id)
        if name is not None:
            row.name = normalize_name(name)
        if description is not None:
            row.description = blank_to_none(description)
        try:
            await self._session.commit()
        except IntegrityError as err:
            await self._session.rollback()
            if is_unique_violation(err):
                raise ConflictError(f'A company named "{row.name}" already exists') from None
            raise
        return (await self.hydrate([row], user_id))[0]
