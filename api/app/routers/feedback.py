from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.deps import CurrentUser, Deps, Session, responses
from app.errors import ConflictError, NotFoundError
from app.feedback.service import FeedbackService, SubmitFeedbackInput
from app.schemas import (
    ListCorrectionsResponseContent,
    SubmitFeedbackRequestContent,
    SubmitFeedbackResponseContent,
    UpdateCorrectionRequestContent,
    UpdateCorrectionResponseContent,
)

router = APIRouter(tags=["Feedback"])
Id = Annotated[str, Path(min_length=1, max_length=64)]


def feedback_service(session: Session, deps: Deps) -> FeedbackService:
    return FeedbackService(session, deps)


Feedback = Annotated[FeedbackService, Depends(feedback_service)]


@router.put(
    "/api/messages/{messageId}/feedback",
    operation_id="SubmitFeedback",
    response_model=SubmitFeedbackResponseContent,
    response_model_exclude_none=True,
    responses=responses(NotFoundError, ConflictError),
)
async def submit_feedback(
    messageId: Id, body: SubmitFeedbackRequestContent, user: CurrentUser, feedback: Feedback
) -> SubmitFeedbackResponseContent:
    correction = await feedback.submit(
        SubmitFeedbackInput(
            message_id=messageId,
            rating=body.rating,
            what_was_wrong=body.whatWasWrong,
            corrected_answer=body.correctedAnswer,
            user_id=user.id,
        )
    )
    return SubmitFeedbackResponseContent(correction=correction)


@router.get(
    "/api/companies/{companyId}/corrections",
    operation_id="ListCorrections",
    response_model=ListCorrectionsResponseContent,
    response_model_exclude_none=True,
    responses=responses(NotFoundError),
)
async def list_corrections(
    companyId: Id,
    user: CurrentUser,
    feedback: Feedback,
    includeInactive: Annotated[bool | None, Query()] = None,
) -> ListCorrectionsResponseContent:
    return ListCorrectionsResponseContent(
        items=await feedback.list_corrections(companyId, bool(includeInactive))
    )


@router.patch(
    "/api/corrections/{correctionId}",
    operation_id="UpdateCorrection",
    response_model=UpdateCorrectionResponseContent,
    response_model_exclude_none=True,
    responses=responses(NotFoundError),
)
async def update_correction(
    correctionId: Id, body: UpdateCorrectionRequestContent, user: CurrentUser, feedback: Feedback
) -> UpdateCorrectionResponseContent:
    return UpdateCorrectionResponseContent(
        correction=await feedback.update_correction(correctionId, body.active)
    )
