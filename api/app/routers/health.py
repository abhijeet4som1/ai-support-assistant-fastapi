from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Response

from app.deps import PUBLIC, respond, responses
from app.schemas import HealthResponseContent

router = APIRouter(tags=["Health"])


@router.get(
    "/api/health",
    operation_id="Health",
    response_model=HealthResponseContent,
    response_model_exclude_none=True,
    responses=responses(),
    openapi_extra=PUBLIC,
)
async def health() -> Response:
    return respond(HealthResponseContent(status="ok", service="api", time=datetime.now(UTC)))
