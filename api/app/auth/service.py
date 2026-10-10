from __future__ import annotations

import asyncio
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import TokenClaims, TokenSigner
from app.auth.password import verify_password
from app.auth.refresh_tokens import RefreshTokenStore
from app.auth.users import AuthUser, find_user_by_id, find_user_by_username, to_auth_user
from app.errors import UnauthorizedError
from app.schemas import TokenSet

_REFRESH_MESSAGES = {
    "unknown": "Invalid refresh token",
    "expired": "Your session has expired. Please log in again.",
    "reused": "This session was revoked because a refresh token was reused. Please log in again.",
    "revoked": "This session has been logged out. Please log in again.",
}


@dataclass
class Session:
    tokens: TokenSet
    user: AuthUser


class AuthService:
    def __init__(self, session: AsyncSession, tokens: TokenSigner, ttl_days: float) -> None:
        self._session = session
        self._tokens = tokens
        self._refresh = RefreshTokenStore(session, ttl_days)

    async def _session_for(self, user_id: UUID, username: str) -> Session:
        user = await find_user_by_id(self._session, user_id)
        if user is None:
            raise UnauthorizedError("User no longer exists")
        access = self._tokens.sign(TokenClaims(sub=str(user.id), username=username))
        refresh = await self._refresh.issue(user.id)
        return Session(
            tokens=TokenSet(
                accessToken=access.token,
                accessExpiresAt=access.expires_at,
                refreshToken=refresh.token,
                refreshExpiresAt=refresh.expires_at,
            ),
            user=to_auth_user(user),
        )

    async def login(self, username: str, password: str) -> Session:
        user = await find_user_by_username(self._session, username)
        # Same error for unknown user and wrong password: do not leak which usernames exist.
        ok = (
            await asyncio.to_thread(verify_password, user.password_hash, password)
            if user
            else False
        )
        if user is None or not ok:
            raise UnauthorizedError("Invalid username or password")
        return await self._session_for(user.id, user.username)

    async def refresh(self, refresh_token: str) -> Session:
        """Rotates a refresh token. Any failure is a 401; reuse revokes the whole family."""
        outcome = await self._refresh.rotate(refresh_token)
        if not outcome.ok or outcome.user_id is None or outcome.next is None:
            raise UnauthorizedError(_REFRESH_MESSAGES[outcome.reason or "unknown"])
        user = await find_user_by_id(self._session, outcome.user_id)
        if user is None:
            raise UnauthorizedError("User no longer exists")
        access = self._tokens.sign(TokenClaims(sub=str(user.id), username=user.username))
        return Session(
            tokens=TokenSet(
                accessToken=access.token,
                accessExpiresAt=access.expires_at,
                refreshToken=outcome.next.token,
                refreshExpiresAt=outcome.next.expires_at,
            ),
            user=to_auth_user(user),
        )

    async def logout(self, refresh_token: str) -> bool:
        return await self._refresh.logout(refresh_token)

    async def authenticate(self, bearer: str | None) -> AuthUser | None:
        """Resolves a bearer access token to a user, or None when missing/invalid/expired/unknown."""
        if not bearer:
            return None
        claims = self._tokens.verify(bearer)
        if claims is None:
            return None
        user = await find_user_by_id(self._session, claims.sub)
        return to_auth_user(user) if user else None


def bearer_from_header(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None
