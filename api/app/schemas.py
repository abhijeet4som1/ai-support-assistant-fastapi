"""Pydantic models = the API contract. Class names and property names match the Smithy-generated
reference document (`packages/openapi/reference-smithy.json`) because the web app imports the
generated TypeScript types by these names. Optional members use `SkipJsonSchema[None]` so the
exported OpenAPI keeps them as plain optional strings (not nullable) and are omitted from JSON
responses (`exclude_none`), exactly like the TypeScript api left them `undefined`."""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema

Id = Annotated[str, Field(min_length=1, max_length=64)]
Cursor = Annotated[str, Field(min_length=1, max_length=512)]


class Model(BaseModel):
    model_config = ConfigDict(extra="ignore")


# --- enums ---------------------------------------------------------------------------------------


class Coverage(str, Enum):
    covered = "covered"
    partial = "partial"
    not_covered = "not_covered"


class FeedbackRating(str, Enum):
    up = "up"
    down = "down"


class GuidelineStatus(str, Enum):
    queued = "queued"
    parsing = "parsing"
    chunking = "chunking"
    embedding = "embedding"
    ready = "ready"
    failed = "failed"
    superseded = "superseded"


class MessageKind(str, Enum):
    customer = "customer"
    instruction = "instruction"


class MessageRole(str, Enum):
    customer = "customer"
    instruction = "instruction"
    assistant = "assistant"


class MessageStatus(str, Enum):
    ok = "ok"
    failed = "failed"


# --- shared shapes -------------------------------------------------------------------------------


class User(Model):
    id: Id
    username: Annotated[str, Field(min_length=1, max_length=200)]
    displayName: Annotated[str, Field(min_length=1, max_length=200)]


class TokenSet(Model):
    """Short-lived access token (JWT, sent as Bearer) plus a long-lived, single-use refresh token.
    Reusing a rotated refresh token revokes the whole session family."""

    accessToken: str
    accessExpiresAt: AwareDatetime
    refreshToken: str
    refreshExpiresAt: AwareDatetime


class GuidelineVersionSummary(Model):
    id: Id
    companyId: Id
    filename: Annotated[str, Field(min_length=1, max_length=200)]
    contentType: str
    sizeBytes: int
    status: GuidelineStatus
    chunksTotal: int
    chunksEmbedded: int
    error: str | SkipJsonSchema[None] = None
    isActive: bool
    uploadedBy: User
    createdAt: AwareDatetime
    updatedAt: AwareDatetime
    readyAt: AwareDatetime | SkipJsonSchema[None] = None
    supersededBy: Id | SkipJsonSchema[None] = None


class Company(Model):
    id: Id
    name: Annotated[str, Field(min_length=1, max_length=200)]
    description: str | SkipJsonSchema[None] = None
    activeGuidelines: GuidelineVersionSummary | SkipJsonSchema[None] = None
    latestGuidelines: GuidelineVersionSummary | SkipJsonSchema[None] = None
    conversationCount: int
    createdAt: AwareDatetime
    updatedAt: AwareDatetime


class GuidelineChunk(Model):
    id: Id
    ordinal: int
    title: str | SkipJsonSchema[None] = None
    content: str
    tokenCount: int


class Citation(Model):
    chunkId: Id
    title: str | SkipJsonSchema[None] = None


class Escalation(Model):
    recommended: bool
    to: str | SkipJsonSchema[None] = None
    reason: str | SkipJsonSchema[None] = None


class AssistantGuidance(Model):
    """Structured guidance produced by the assistant for the agent."""

    coverage: Coverage
    recommendedReply: str = Field(
        description="Customer-facing draft; placeholders like [Name] are left for the agent."
    )
    handlingSteps: list[str] = Field(description="Internal steps for the agent, in order.")
    clarifications: list[str] | SkipJsonSchema[None] = Field(
        default=None,
        description="Questions the customer must answer before the case can be resolved\n"
        "(preferences, missing details). Optional for older messages.",
    )
    agentDecisions: list[str] = Field(
        description="Decisions the guidelines leave to the agent's judgement "
        "(never questions for the customer)."
    )
    escalation: Escalation
    citations: list[Citation]
    notes: str | SkipJsonSchema[None] = None


class RetrievedChunk(Model):
    chunkId: Id
    title: str | SkipJsonSchema[None] = None
    score: float


class UsedCorrection(Model):
    correctionId: Id
    score: float


class FeedbackSummary(Model):
    """Feedback the current or another user left on an assistant message."""

    id: Id
    rating: FeedbackRating
    whatWasWrong: str | SkipJsonSchema[None] = None
    correctedAnswer: str | SkipJsonSchema[None] = None
    user: User
    createdAt: AwareDatetime


class Message(Model):
    id: Id
    conversationId: Id
    role: MessageRole
    content: str = Field(
        description="Raw text for customer/instruction messages; the recommended reply for\n"
        "assistant messages (full structure in `guidance`)."
    )
    status: MessageStatus
    error: str | SkipJsonSchema[None] = None
    guidance: AssistantGuidance | SkipJsonSchema[None] = None
    retrieval: list[RetrievedChunk] | SkipJsonSchema[None] = None
    correctionsUsed: list[UsedCorrection] | SkipJsonSchema[None] = None
    guidelineVersionId: Id | SkipJsonSchema[None] = None
    model: str | SkipJsonSchema[None] = None
    promptTokens: int | SkipJsonSchema[None] = Field(
        default=None,
        description="Tokens in the prompt (system instruction, history, retrieved context).",
    )
    completionTokens: int | SkipJsonSchema[None] = Field(
        default=None, description="Visible answer tokens, excluding the model's reasoning."
    )
    thinkingTokens: int | SkipJsonSchema[None] = Field(
        default=None,
        description='Reasoning ("thinking") tokens; billed as output but not part of the answer.',
    )
    totalTokens: int | SkipJsonSchema[None] = Field(
        default=None,
        description="Total tokens billed for the call as reported by the provider "
        "(prompt + thinking + answer).",
    )
    latencyMs: int | SkipJsonSchema[None] = None
    feedback: list[FeedbackSummary] | SkipJsonSchema[None] = None
    createdBy: User
    createdAt: AwareDatetime


class ConversationSummary(Model):
    id: Id
    companyId: Id
    companyName: Annotated[str, Field(min_length=1, max_length=200)]
    title: str
    messageCount: int
    lastCoverage: Coverage | SkipJsonSchema[None] = None
    createdBy: User
    createdAt: AwareDatetime
    lastMessageAt: AwareDatetime


class Conversation(Model):
    summary: ConversationSummary
    messages: list[Message]


class Correction(Model):
    """A stored piece of feedback, used as a few-shot correction for future answers."""

    id: Id
    companyId: Id
    conversationId: Id
    messageId: Id
    rating: FeedbackRating
    queryText: str = Field(description="The customer message that led to the flagged answer.")
    whatWasWrong: str | SkipJsonSchema[None] = None
    correctedAnswer: str | SkipJsonSchema[None] = None
    guidelineVersionId: Id
    active: bool = Field(
        description="Inactive corrections are not retrieved (e.g. tied to replaced guidelines)."
    )
    user: User
    createdAt: AwareDatetime


# --- operation inputs and outputs ----------------------------------------------------------------


class HealthResponseContent(Model):
    status: str
    service: str
    time: AwareDatetime


class LoginRequestContent(Model):
    username: Annotated[str, Field(min_length=1, max_length=100)]
    password: Annotated[str, Field(min_length=1, max_length=200)]


class LoginResponseContent(Model):
    tokens: TokenSet
    user: User


class RefreshTokenRequestContent(Model):
    refreshToken: Annotated[str, Field(min_length=1, max_length=512)]


class RefreshTokenResponseContent(Model):
    tokens: TokenSet
    user: User


class LogoutRequestContent(Model):
    refreshToken: Annotated[str, Field(min_length=1, max_length=512)]


class LogoutResponseContent(Model):
    revoked: bool


class GetCurrentUserResponseContent(Model):
    user: User


class ListCompaniesResponseContent(Model):
    items: list[Company]


class CreateCompanyRequestContent(Model):
    name: Annotated[str, Field(min_length=1, max_length=200)]
    description: Annotated[str, Field(max_length=1000)] | SkipJsonSchema[None] = None


class CreateCompanyResponseContent(Model):
    company: Company


class GetCompanyResponseContent(Model):
    company: Company


class UpdateCompanyRequestContent(Model):
    name: Annotated[str, Field(min_length=1, max_length=200)] | SkipJsonSchema[None] = None
    description: Annotated[str, Field(max_length=1000)] | SkipJsonSchema[None] = None


class UpdateCompanyResponseContent(Model):
    company: Company


class UploadGuidelinesResponseContent(Model):
    version: GuidelineVersionSummary


class GetActiveGuidelinesResponseContent(Model):
    version: GuidelineVersionSummary
    text: str
    chunks: list[GuidelineChunk]


class ListGuidelineVersionsResponseContent(Model):
    items: list[GuidelineVersionSummary]


class GetGuidelineVersionResponseContent(Model):
    version: GuidelineVersionSummary


class RetryGuidelineVersionResponseContent(Model):
    version: GuidelineVersionSummary


class ActivateGuidelineVersionResponseContent(Model):
    version: GuidelineVersionSummary


class CreateConversationRequestContent(Model):
    companyId: Id


class CreateConversationResponseContent(Model):
    conversation: Conversation


class ListConversationsResponseContent(Model):
    items: list[ConversationSummary]
    nextCursor: Cursor | SkipJsonSchema[None] = Field(
        default=None, description="Cursor for paginated list operations (opaque to clients)."
    )


class GetConversationResponseContent(Model):
    conversation: Conversation
    olderCursor: Cursor | SkipJsonSchema[None] = Field(
        default=None,
        description="Present when older messages exist; pass it as `before` to load them.",
    )


class SendMessageRequestContent(Model):
    kind: MessageKind
    content: Annotated[str, Field(min_length=1, max_length=20000)]


class SendMessageResponseContent(Model):
    userMessage: Message
    assistantMessage: Message


class SubmitFeedbackRequestContent(Model):
    rating: FeedbackRating
    whatWasWrong: Annotated[str, Field(max_length=5000)] | SkipJsonSchema[None] = None
    correctedAnswer: Annotated[str, Field(max_length=20000)] | SkipJsonSchema[None] = None


class SubmitFeedbackResponseContent(Model):
    correction: Correction


class ListCorrectionsResponseContent(Model):
    items: list[Correction]


class UpdateCorrectionRequestContent(Model):
    active: bool


class UpdateCorrectionResponseContent(Model):
    correction: Correction


# --- error bodies (documented per operation; raised through app.errors) --------------------------


class ValidationExceptionField(Model):
    """Describes one specific validation failure for an input member."""

    path: str = Field(
        description="A JSONPointer expression to the structure member whose value failed to "
        "satisfy the modeled constraints."
    )
    message: str = Field(description="A detailed description of the validation failure.")


class ValidationExceptionResponseContent(Model):
    """A standard error for input validation failures."""

    message: str = Field(description="A summary of the validation failure.")
    fieldList: list[ValidationExceptionField] | SkipJsonSchema[None] = Field(
        default=None,
        description="A list of specific failures encountered while validating the input.",
    )


class UnauthorizedErrorResponseContent(Model):
    message: str


class NotFoundErrorResponseContent(Model):
    message: str
    resource: str | SkipJsonSchema[None] = None
    id: str | SkipJsonSchema[None] = None


class ConflictErrorResponseContent(Model):
    """Generic conflict (e.g. duplicate company name)."""

    message: str


class GuidelinesNotReadyErrorResponseContent(Model):
    message: str
    companyId: Id
    latestStatus: GuidelineStatus | SkipJsonSchema[None] = None


class GuidelinesConflictErrorResponseContent(Model):
    """Another user uploaded guidelines after the client loaded the page."""

    message: str
    latestVersionId: Id
    uploadedBy: User
    uploadedAt: AwareDatetime


class PayloadTooLargeErrorResponseContent(Model):
    message: str
    maxBytes: int


class UnsupportedMediaTypeErrorResponseContent(Model):
    message: str
    supported: list[str]


class RateLimitedErrorResponseContent(Model):
    message: str
    retryAfterSeconds: int | SkipJsonSchema[None] = None


class AiProviderErrorResponseContent(Model):
    """The AI provider failed or timed out. Safe to retry."""

    message: str
    provider: str | SkipJsonSchema[None] = None


class InternalServerErrorResponseContent(Model):
    message: str
    requestId: str | SkipJsonSchema[None] = None
