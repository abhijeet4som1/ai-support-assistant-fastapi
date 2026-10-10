"""Opaque refresh tokens with rotation and reuse detection.
- The raw token is random and only its SHA-256 hash is stored.
- Every refresh revokes the presented token and issues a new one in the same family.
- Presenting a token that was already rotated means it leaked: the whole family is revoked."""

from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RefreshToken


@dataclass
class IssuedRefreshToken:
    token: str
    expires_at: datetime
    family_id: UUID


@dataclass
class RefreshOutcome:
    ok: bool
    user_id: UUID | None = None
    next: IssuedRefreshToken | None = None
    reason: Literal["unknown", "expired", "reused", "revoked"] | None = None


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class RefreshTokenStore:
    def __init__(self, session: AsyncSession, ttl_days: float) -> None:
        self._session = session
        self._ttl = timedelta(days=ttl_days)

    async def issue(self, user_id: UUID, family_id: UUID | None = None) -> IssuedRefreshToken:
        token = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
        expires_at = datetime.now(UTC) + self._ttl
        family = family_id or uuid4()
        self._session.add(
            RefreshToken(
                user_id=user_id, family_id=family, token_hash=_hash(token), expires_at=expires_at
            )
        )
        await self._session.commit()
        return IssuedRefreshToken(token, expires_at.replace(microsecond=0), family)

    async def revoke_family(self, family_id: UUID) -> None:
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
        await self._session.commit()

    async def rotate(self, token: str) -> RefreshOutcome:
        row = await self._session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == _hash(token))
        )
        if row is None:
            return RefreshOutcome(ok=False, reason="unknown")
        if row.revoked_at is not None:
            # Already rotated or logged out. If it was rotated, someone is replaying an old token.
            await self.revoke_family(row.family_id)
            return RefreshOutcome(ok=False, reason="reused" if row.replaced_by else "revoked")
        if row.expires_at <= datetime.now(UTC):
            return RefreshOutcome(ok=False, reason="expired")
        nxt = await self.issue(row.user_id, row.family_id)
        next_id = await self._session.scalar(
            select(RefreshToken.id).where(RefreshToken.token_hash == _hash(nxt.token))
        )
        row.revoked_at = datetime.now(UTC)
        row.replaced_by = next_id
        await self._session.commit()
        return RefreshOutcome(ok=True, user_id=row.user_id, next=nxt)

    async def logout(self, token: str) -> bool:
        """Revokes the family of the given token. Returns False when the token is unknown."""
        row = await self._session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == _hash(token))
        )
        if row is None:
            return False
        await self.revoke_family(row.family_id)
        return True
