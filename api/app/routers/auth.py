from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.service import AuthService
from app.deps import PUBLIC, CurrentUser, auth_service, responses
from app.schemas import (
    GetCurrentUserResponseContent,
    LoginRequestContent,
    LoginResponseContent,
    LogoutRequestContent,
    LogoutResponseContent,
    RefreshTokenRequestContent,
    RefreshTokenResponseContent,
)

router = APIRouter(tags=["Auth"])
Auth = Annotated[AuthService, Depends(auth_service)]


@router.post(
    "/api/auth/login",
    operation_id="Login",
    response_model=LoginResponseContent,
    response_model_exclude_none=True,
    responses=responses(),
    openapi_extra=PUBLIC,
)
async def login(body: LoginRequestContent, auth: Auth) -> LoginResponseContent:
    session = await auth.login(body.username, body.password)
    return LoginResponseContent(tokens=session.tokens, user=session.user.schema())


@router.post(
    "/api/auth/refresh",
    operation_id="RefreshToken",
    response_model=RefreshTokenResponseContent,
    response_model_exclude_none=True,
    responses=responses(),
    openapi_extra=PUBLIC,
)
async def refresh(body: RefreshTokenRequestContent, auth: Auth) -> RefreshTokenResponseContent:
    session = await auth.refresh(body.refreshToken)
    return RefreshTokenResponseContent(tokens=session.tokens, user=session.user.schema())


@router.post(
    "/api/auth/logout",
    operation_id="Logout",
    response_model=LogoutResponseContent,
    response_model_exclude_none=True,
    responses=responses(),
    openapi_extra=PUBLIC,
)
async def logout(body: LogoutRequestContent, auth: Auth) -> LogoutResponseContent:
    return LogoutResponseContent(revoked=await auth.logout(body.refreshToken))


@router.get(
    "/api/auth/me",
    operation_id="GetCurrentUser",
    response_model=GetCurrentUserResponseContent,
    response_model_exclude_none=True,
    responses=responses(),
)
async def me(user: CurrentUser) -> GetCurrentUserResponseContent:
    return GetCurrentUserResponseContent(user=user.schema())
