from __future__ import annotations

import asyncio
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.password import hash_password
from app.db.models import User
from app.schemas import User as UserSchema


@dataclass
class AuthUser:
    id: str
    username: str
    displayName: str

    def schema(self) -> UserSchema:
        return UserSchema(id=self.id, username=self.username, displayName=self.displayName)


def to_auth_user(u: User) -> AuthUser:
    return AuthUser(id=str(u.id), username=u.username, displayName=u.display_name)


def to_user_schema(u: User) -> UserSchema:
    return UserSchema(id=str(u.id), username=u.username, displayName=u.display_name)


async def find_user_by_username(session: AsyncSession, username: str) -> User | None:
    return await session.scalar(select(User).where(User.username == username))


async def find_user_by_id(session: AsyncSession, user_id: str | UUID) -> User | None:
    try:
        uid = user_id if isinstance(user_id, UUID) else UUID(user_id)
    except ValueError:
        return None
    return await session.get(User, uid)


@dataclass
class SeedUser:
    username: str
    password: str


def parse_seed_users(spec: str) -> list[SeedUser]:
    """Parses `user:password,user2:password2`."""
    out: list[SeedUser] = []
    for raw in spec.split(","):
        pair = raw.strip()
        if not pair:
            continue
        idx = pair.find(":")
        if idx <= 0 or idx == len(pair) - 1:
            raise ValueError(f'SEED_USERS entry "{pair}" must look like username:password')
        out.append(SeedUser(pair[:idx], pair[idx + 1 :]))
    return out


async def seed_users(session: AsyncSession, spec: str) -> list[str]:
    """Creates seed users that do not exist yet; never overwrites an existing password."""
    created: list[str] = []
    for entry in parse_seed_users(spec):
        if await find_user_by_username(session, entry.username):
            continue
        password_hash = await asyncio.to_thread(hash_password, entry.password)
        session.add(
            User(
                username=entry.username,
                password_hash=password_hash,
                display_name=entry.username[:1].upper() + entry.username[1:],
            )
        )
        await session.commit()
        created.append(entry.username)
    return created
