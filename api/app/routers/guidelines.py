from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Path, Request

from app.deps import CurrentUser, Deps, Session, responses
from app.errors import (
    ConflictError,
    GuidelinesConflictError,
    GuidelinesNotReadyError,
    NotFoundError,
    PayloadTooLargeError,
    UnsupportedMediaTypeError,
)
from app.guidelines.service import GuidelinesService, UploadInput
from app.schemas import (
    ActivateGuidelineVersionResponseContent,
    GetActiveGuidelinesResponseContent,
    GetGuidelineVersionResponseContent,
    ListGuidelineVersionsResponseContent,
    RetryGuidelineVersionResponseContent,
    UploadGuidelinesResponseContent,
)

router = APIRouter(tags=["Guidelines"])
CompanyId = Annotated[str, Path(min_length=1, max_length=64)]
VersionId = Annotated[str, Path(min_length=1, max_length=64)]


def guidelines_service(session: Session, deps: Deps) -> GuidelinesService:
    return GuidelinesService(session, deps.queue, max_upload_bytes=deps.config.max_upload_bytes)


Guidelines = Annotated[GuidelinesService, Depends(guidelines_service)]

UPLOAD_BODY = {
    "requestBody": {
        "required": True,
        "content": {
            "application/octet-stream": {
                "schema": {"$ref": "#/components/schemas/UploadGuidelinesInputPayload"}
            }
        },
    }
}


async def read_raw_body(request: Request, max_bytes: int) -> bytes:
    """Reads the raw upload, refusing bodies well beyond the configured limit early."""
    limit = max_bytes + 64 * 1024
    chunks: list[bytes] = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > limit:
            raise PayloadTooLargeError(
                f"File is larger than the {round(max_bytes / 1024 / 1024)} MB limit",
                max_bytes=max_bytes,
            )
        chunks.append(chunk)
    return b"".join(chunks)


@router.put(
    "/api/companies/{companyId}/guidelines",
    operation_id="UploadGuidelines",
    status_code=202,
    response_model=UploadGuidelinesResponseContent,
    response_model_exclude_none=True,
    responses=responses(
        NotFoundError, GuidelinesConflictError, PayloadTooLargeError, UnsupportedMediaTypeError
    ),
    openapi_extra=UPLOAD_BODY,
)
async def upload_guidelines(
    request: Request,
    companyId: CompanyId,
    user: CurrentUser,
    guidelines: Guidelines,
    deps: Deps,
    x_filename: Annotated[
        str,
        Header(
            alias="X-Filename",
            min_length=1,
            max_length=255,
            description="Original file name (extension is used to pick the parser).",
        ),
    ],
    x_file_content_type: Annotated[
        str | None,
        Header(
            alias="X-File-Content-Type",
            description="Original MIME type as reported by the browser, if known.",
        ),
    ] = None,
    x_expected_version: Annotated[
        str | None,
        Header(
            alias="X-Expected-Version",
            min_length=1,
            max_length=64,
            description="Id of the latest guideline version the client displayed. If a newer\n"
            "version exists the upload is rejected with GuidelinesConflictError.",
        ),
    ] = None,
) -> UploadGuidelinesResponseContent:
    body = await read_raw_body(request, deps.config.max_upload_bytes)
    result = await guidelines.upload(
        UploadInput(
            company_id=companyId,
            filename=x_filename,
            file_content_type=x_file_content_type,
            expected_version_id=x_expected_version,
            body=body,
            user_id=user.id,
        )
    )
    return UploadGuidelinesResponseContent(version=result.version)


@router.get(
    "/api/companies/{companyId}/guidelines",
    operation_id="GetActiveGuidelines",
    response_model=GetActiveGuidelinesResponseContent,
    response_model_exclude_none=True,
    responses=responses(NotFoundError, GuidelinesNotReadyError),
)
async def get_active_guidelines(
    companyId: CompanyId, user: CurrentUser, guidelines: Guidelines
) -> GetActiveGuidelinesResponseContent:
    active = await guidelines.get_active(companyId)
    return GetActiveGuidelinesResponseContent(
        version=active.version, text=active.text, chunks=active.chunks
    )


@router.get(
    "/api/companies/{companyId}/guidelines/versions",
    operation_id="ListGuidelineVersions",
    response_model=ListGuidelineVersionsResponseContent,
    response_model_exclude_none=True,
    responses=responses(NotFoundError),
)
async def list_guideline_versions(
    companyId: CompanyId, user: CurrentUser, guidelines: Guidelines
) -> ListGuidelineVersionsResponseContent:
    return ListGuidelineVersionsResponseContent(items=await guidelines.list_versions(companyId))


@router.get(
    "/api/guideline-versions/{versionId}",
    operation_id="GetGuidelineVersion",
    response_model=GetGuidelineVersionResponseContent,
    response_model_exclude_none=True,
    responses=responses(NotFoundError),
)
async def get_guideline_version(
    versionId: VersionId, user: CurrentUser, guidelines: Guidelines
) -> GetGuidelineVersionResponseContent:
    return GetGuidelineVersionResponseContent(version=await guidelines.get_version(versionId))


@router.post(
    "/api/guideline-versions/{versionId}/retry",
    operation_id="RetryGuidelineVersion",
    response_model=RetryGuidelineVersionResponseContent,
    response_model_exclude_none=True,
    responses=responses(NotFoundError, ConflictError),
)
async def retry_guideline_version(
    versionId: VersionId, user: CurrentUser, guidelines: Guidelines
) -> RetryGuidelineVersionResponseContent:
    return RetryGuidelineVersionResponseContent(version=await guidelines.retry(versionId))


@router.post(
    "/api/guideline-versions/{versionId}/activate",
    operation_id="ActivateGuidelineVersion",
    response_model=ActivateGuidelineVersionResponseContent,
    response_model_exclude_none=True,
    responses=responses(NotFoundError, ConflictError),
)
async def activate_guideline_version(
    versionId: VersionId, user: CurrentUser, guidelines: Guidelines
) -> ActivateGuidelineVersionResponseContent:
    return ActivateGuidelineVersionResponseContent(version=await guidelines.activate(versionId))
