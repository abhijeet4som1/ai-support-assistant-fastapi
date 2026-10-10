from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.conversations.service import ConversationsService, ListArgs
from app.deps import CurrentUser, Deps, Session, responses
from app.errors import AiProviderError, GuidelinesNotReadyError, NotFoundError
from app.schemas import (
    Coverage,
    CreateConversationRequestContent,
    CreateConversationResponseContent,
    GetConversationResponseContent,
    ListConversationsResponseContent,
    SendMessageRequestContent,
    SendMessageResponseContent,
)

router = APIRouter(tags=["Conversations"])
ConversationId = Annotated[str, Path(min_length=1, max_length=64)]


def conversations_service(session: Session, deps: Deps) -> ConversationsService:
    return ConversationsService(session, deps)


Conversations = Annotated[ConversationsService, Depends(conversations_service)]


@router.post(
    "/api/conversations",
    operation_id="CreateConversation",
    status_code=201,
    response_model=CreateConversationResponseContent,
    response_model_exclude_none=True,
    responses=responses(NotFoundError, GuidelinesNotReadyError),
)
async def create_conversation(
    body: CreateConversationRequestContent, user: CurrentUser, conversations: Conversations
) -> CreateConversationResponseContent:
    return CreateConversationResponseContent(
        conversation=await conversations.create(body.companyId, user.id)
    )


@router.get(
    "/api/conversations",
    operation_id="ListConversations",
    response_model=ListConversationsResponseContent,
    response_model_exclude_none=True,
    responses=responses(),
)
async def list_conversations(
    user: CurrentUser,
    conversations: Conversations,
    companyId: Annotated[str | None, Query(min_length=1, max_length=64)] = None,
    coverage: Annotated[Coverage | None, Query()] = None,
    cursor: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=512,
            description="Cursor for paginated list operations (opaque to clients).",
        ),
    ] = None,
    limit: Annotated[int | None, Query(ge=1, le=100)] = None,
) -> ListConversationsResponseContent:
    result = await conversations.list(
        ListArgs(
            user_id=user.id, company_id=companyId, coverage=coverage, cursor=cursor, limit=limit
        )
    )
    return ListConversationsResponseContent(items=result.items, nextCursor=result.next_cursor)


@router.get(
    "/api/conversations/{conversationId}",
    operation_id="GetConversation",
    response_model=GetConversationResponseContent,
    response_model_exclude_none=True,
    responses=responses(NotFoundError),
)
async def get_conversation(
    conversationId: ConversationId,
    user: CurrentUser,
    conversations: Conversations,
    before: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=512,
            description="Load messages older than this cursor (from a previous page's `olderCursor`).",
        ),
    ] = None,
    limit: Annotated[
        int | None, Query(ge=1, le=100, description="Messages per page (default 50).")
    ] = None,
) -> GetConversationResponseContent:
    page = await conversations.get(conversationId, user.id, before=before, limit=limit)
    return GetConversationResponseContent(
        conversation=page.conversation, olderCursor=page.older_cursor
    )


@router.post(
    "/api/conversations/{conversationId}/messages",
    operation_id="SendMessage",
    status_code=201,
    response_model=SendMessageResponseContent,
    response_model_exclude_none=True,
    responses=responses(NotFoundError, GuidelinesNotReadyError, AiProviderError),
)
async def send_message(
    conversationId: ConversationId,
    body: SendMessageRequestContent,
    user: CurrentUser,
    conversations: Conversations,
) -> SendMessageResponseContent:
    sent = await conversations.send_message(
        conversation_id=conversationId, kind=body.kind, content=body.content, user_id=user.id
    )
    return SendMessageResponseContent(
        userMessage=sent.user_message, assistantMessage=sent.assistant_message
    )
