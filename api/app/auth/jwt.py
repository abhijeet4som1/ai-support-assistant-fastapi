"""HS256 access tokens: 15 minutes by default, issuer `ai-support-assistant`, unique jti."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt

ISSUER = "ai-support-assistant"


@dataclass
class TokenClaims:
    sub: str
    username: str


@dataclass
class SignedToken:
    token: str
    expires_at: datetime


class TokenSigner:
    def __init__(self, secret: str, ttl_minutes: float) -> None:
        self._secret = secret
        self._ttl = timedelta(minutes=ttl_minutes)

    def sign(self, claims: TokenClaims) -> SignedToken:
        now = datetime.now(UTC)
        expires_at = now + self._ttl
        token = jwt.encode(
            {
                "username": claims.username,
                "sub": claims.sub,
                "jti": str(uuid4()),  # unique per token even when issued within the same second
                "iss": ISSUER,
                "iat": int(now.timestamp()),
                "exp": int(expires_at.timestamp()),
            },
            self._secret,
            algorithm="HS256",
        )
        return SignedToken(token, expires_at.replace(microsecond=0))

    def verify(self, token: str) -> TokenClaims | None:
        """Returns the claims, or None when the token is invalid, expired or not issued by us."""
        try:
            payload = jwt.decode(token, self._secret, algorithms=["HS256"], issuer=ISSUER)
        except jwt.PyJWTError:
            return None
        sub, username = payload.get("sub"), payload.get("username")
        if not isinstance(sub, str) or not isinstance(username, str):
            return None
        return TokenClaims(sub=sub, username=username)
