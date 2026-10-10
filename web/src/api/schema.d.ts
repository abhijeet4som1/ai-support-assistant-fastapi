export interface paths {
    "/api/auth/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** @description Exchange username + password for a token set. Public. */
        post: operations["Login"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/auth/logout": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** @description Revoke the session family of a refresh token. Public; unknown tokens are ignored. */
        post: operations["Logout"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/auth/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** @description Returns the user identified by the bearer token. */
        get: operations["GetCurrentUser"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/auth/refresh": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** @description Rotate a refresh token into a new token set. Public (the refresh token is the credential). */
        post: operations["RefreshToken"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/companies": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["ListCompanies"];
        put?: never;
        post: operations["CreateCompany"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/companies/{companyId}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["GetCompany"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch: operations["UpdateCompany"];
        trace?: never;
    };
    "/api/companies/{companyId}/corrections": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["ListCorrections"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/companies/{companyId}/guidelines": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** @description The active guideline version with its extracted text and chunks. */
        get: operations["GetActiveGuidelines"];
        /**
         * @description Upload (or replace) the guideline file for a company. Processing is
         *     asynchronous: returns 202 with the new version in `queued` status; poll
         *     GetGuidelineVersion until it is `ready`, `failed` or `superseded`.
         */
        put: operations["UploadGuidelines"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/companies/{companyId}/guidelines/versions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["ListGuidelineVersions"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/conversations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * @description Lists the calling agent's own conversations, newest activity first. Conversations are private
         *     to the agent who started them.
         */
        get: operations["ListConversations"];
        put?: never;
        post: operations["CreateConversation"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/conversations/{conversationId}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * @description Returns the conversation with its newest messages (chronological order). Long threads are
         *     paged: pass `before` (the `olderCursor` of a previous page) to load the messages preceding it.
         */
        get: operations["GetConversation"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/conversations/{conversationId}/messages": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * @description Append a customer message or an agent instruction and get the assistant's
         *     guidance. Both the user message and the assistant message are persisted,
         *     even when the AI provider fails (assistant message has status `failed`).
         */
        post: operations["SendMessage"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/corrections/{correctionId}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** @description Activate or deactivate a correction. */
        patch: operations["UpdateCorrection"];
        trace?: never;
    };
    "/api/guideline-versions/{versionId}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** @description Status + progress of one version. Poll while status is not terminal. */
        get: operations["GetGuidelineVersion"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/guideline-versions/{versionId}/activate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** @description Make a `ready` version the active one (rollback / conflict resolution). */
        post: operations["ActivateGuidelineVersion"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/guideline-versions/{versionId}/retry": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** @description Re-enqueue a failed version. */
        post: operations["RetryGuidelineVersion"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** @description Liveness probe. Public. */
        get: operations["Health"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/messages/{messageId}/feedback": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** @description Rate an assistant message. A thumbs-down requires the corrected answer. */
        put: operations["SubmitFeedback"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        ActivateGuidelineVersionResponseContent: {
            version: components["schemas"]["GuidelineVersionSummary"];
        };
        /** @description The AI provider failed or timed out. Safe to retry. */
        AiProviderErrorResponseContent: {
            message: string;
            provider?: string;
        };
        /** @description Structured guidance produced by the assistant for the agent. */
        AssistantGuidance: {
            coverage: components["schemas"]["Coverage"];
            /** @description Customer-facing draft; placeholders like [Name] are left for the agent. */
            recommendedReply: string;
            /** @description Internal steps for the agent, in order. */
            handlingSteps: string[];
            /**
             * @description Questions the customer must answer before the case can be resolved
             *     (preferences, missing details). Optional for older messages.
             */
            clarifications?: string[];
            /** @description Decisions the guidelines leave to the agent's judgement (never questions for the customer). */
            agentDecisions: string[];
            escalation: components["schemas"]["Escalation"];
            citations: components["schemas"]["Citation"][];
            notes?: string;
        };
        Citation: {
            chunkId: string;
            title?: string;
        };
        Company: {
            id: string;
            name: string;
            description?: string;
            activeGuidelines?: components["schemas"]["GuidelineVersionSummary"];
            latestGuidelines?: components["schemas"]["GuidelineVersionSummary"];
            /** Format: int32 */
            conversationCount: number;
            /**
             * Format: date-time
             * @description ISO-8601 date-time (restJson1 would otherwise default to epoch seconds).
             */
            createdAt: string;
            /**
             * Format: date-time
             * @description ISO-8601 date-time (restJson1 would otherwise default to epoch seconds).
             */
            updatedAt: string;
        };
        /** @description Generic conflict (e.g. duplicate company name). */
        ConflictErrorResponseContent: {
            message: string;
        };
        Conversation: {
            summary: components["schemas"]["ConversationSummary"];
            messages: components["schemas"]["Message"][];
        };
        ConversationSummary: {
            id: string;
            companyId: string;
            companyName: string;
            title: string;
            /** Format: int32 */
            messageCount: number;
            lastCoverage?: components["schemas"]["Coverage"];
            createdBy: components["schemas"]["User"];
            /**
             * Format: date-time
             * @description ISO-8601 date-time (restJson1 would otherwise default to epoch seconds).
             */
            createdAt: string;
            /**
             * Format: date-time
             * @description ISO-8601 date-time (restJson1 would otherwise default to epoch seconds).
             */
            lastMessageAt: string;
        };
        /** @description A stored piece of feedback, used as a few-shot correction for future answers. */
        Correction: {
            id: string;
            companyId: string;
            conversationId: string;
            messageId: string;
            rating: components["schemas"]["FeedbackRating"];
            /** @description The customer message that led to the flagged answer. */
            queryText: string;
            whatWasWrong?: string;
            correctedAnswer?: string;
            guidelineVersionId: string;
            /** @description Inactive corrections are not retrieved (e.g. tied to replaced guidelines). */
            active: boolean;
            user: components["schemas"]["User"];
            /**
             * Format: date-time
             * @description ISO-8601 date-time (restJson1 would otherwise default to epoch seconds).
             */
            createdAt: string;
        };
        /** @enum {string} */
        Coverage: "covered" | "partial" | "not_covered";
        CreateCompanyRequestContent: {
            name: string;
            description?: string;
        };
        CreateCompanyResponseContent: {
            company: components["schemas"]["Company"];
        };
        CreateConversationRequestContent: {
            companyId: string;
        };
        CreateConversationResponseContent: {
            conversation: components["schemas"]["Conversation"];
        };
        Escalation: {
            recommended: boolean;
            to?: string;
            reason?: string;
        };
        /** @enum {string} */
        FeedbackRating: "up" | "down";
        /** @description Feedback the current or another user left on an assistant message. */
        FeedbackSummary: {
            id: string;
            rating: components["schemas"]["FeedbackRating"];
            whatWasWrong?: string;
            correctedAnswer?: string;
            user: components["schemas"]["User"];
            /**
             * Format: date-time
             * @description ISO-8601 date-time (restJson1 would otherwise default to epoch seconds).
             */
            createdAt: string;
        };
        GetActiveGuidelinesResponseContent: {
            version: components["schemas"]["GuidelineVersionSummary"];
            text: string;
            chunks: components["schemas"]["GuidelineChunk"][];
        };
        GetCompanyResponseContent: {
            company: components["schemas"]["Company"];
        };
        GetConversationResponseContent: {
            conversation: components["schemas"]["Conversation"];
            /** @description Present when older messages exist; pass it as `before` to load them. */
            olderCursor?: string;
        };
        GetCurrentUserResponseContent: {
            user: components["schemas"]["User"];
        };
        GetGuidelineVersionResponseContent: {
            version: components["schemas"]["GuidelineVersionSummary"];
        };
        GuidelineChunk: {
            id: string;
            /** Format: int32 */
            ordinal: number;
            title?: string;
            content: string;
            /** Format: int32 */
            tokenCount: number;
        };
        /**
         * @description Lifecycle of an uploaded guideline file.
         * @enum {string}
         */
        GuidelineStatus: "queued" | "parsing" | "chunking" | "embedding" | "ready" | "failed" | "superseded";
        GuidelineVersionSummary: {
            id: string;
            companyId: string;
            filename: string;
            contentType: string;
            /** Format: int32 */
            sizeBytes: number;
            status: components["schemas"]["GuidelineStatus"];
            /** Format: int32 */
            chunksTotal: number;
            /** Format: int32 */
            chunksEmbedded: number;
            error?: string;
            isActive: boolean;
            uploadedBy: components["schemas"]["User"];
            /**
             * Format: date-time
             * @description ISO-8601 date-time (restJson1 would otherwise default to epoch seconds).
             */
            createdAt: string;
            /**
             * Format: date-time
             * @description ISO-8601 date-time (restJson1 would otherwise default to epoch seconds).
             */
            updatedAt: string;
            /**
             * Format: date-time
             * @description ISO-8601 date-time (restJson1 would otherwise default to epoch seconds).
             */
            readyAt?: string;
            supersededBy?: string;
        };
        /** @description Another user uploaded guidelines after the client loaded the page. */
        GuidelinesConflictErrorResponseContent: {
            message: string;
            latestVersionId: string;
            uploadedBy: components["schemas"]["User"];
            /**
             * Format: date-time
             * @description ISO-8601 date-time (restJson1 would otherwise default to epoch seconds).
             */
            uploadedAt: string;
        };
        GuidelinesNotReadyErrorResponseContent: {
            message: string;
            companyId: string;
            latestStatus?: components["schemas"]["GuidelineStatus"];
        };
        HealthResponseContent: {
            status: string;
            service: string;
            /**
             * Format: date-time
             * @description ISO-8601 date-time (restJson1 would otherwise default to epoch seconds).
             */
            time: string;
        };
        InternalServerErrorResponseContent: {
            message: string;
            requestId?: string;
        };
        ListCompaniesResponseContent: {
            items: components["schemas"]["Company"][];
        };
        ListConversationsResponseContent: {
            items: components["schemas"]["ConversationSummary"][];
            /** @description Cursor for paginated list operations (opaque to clients). */
            nextCursor?: string;
        };
        ListCorrectionsResponseContent: {
            items: components["schemas"]["Correction"][];
        };
        ListGuidelineVersionsResponseContent: {
            items: components["schemas"]["GuidelineVersionSummary"][];
        };
        LoginRequestContent: {
            username: string;
            password: string;
        };
        LoginResponseContent: {
            tokens: components["schemas"]["TokenSet"];
            user: components["schemas"]["User"];
        };
        LogoutRequestContent: {
            refreshToken: string;
        };
        LogoutResponseContent: {
            revoked: boolean;
        };
        Message: {
            id: string;
            conversationId: string;
            role: components["schemas"]["MessageRole"];
            /**
             * @description Raw text for customer/instruction messages; the recommended reply for
             *     assistant messages (full structure in `guidance`).
             */
            content: string;
            status: components["schemas"]["MessageStatus"];
            error?: string;
            guidance?: components["schemas"]["AssistantGuidance"];
            retrieval?: components["schemas"]["RetrievedChunk"][];
            correctionsUsed?: components["schemas"]["UsedCorrection"][];
            guidelineVersionId?: string;
            model?: string;
            /**
             * Format: int32
             * @description Tokens in the prompt (system instruction, history, retrieved context).
             */
            promptTokens?: number;
            /**
             * Format: int32
             * @description Visible answer tokens, excluding the model's reasoning.
             */
            completionTokens?: number;
            /**
             * Format: int32
             * @description Reasoning ("thinking") tokens; billed as output but not part of the answer.
             */
            thinkingTokens?: number;
            /**
             * Format: int32
             * @description Total tokens billed for the call as reported by the provider (prompt + thinking + answer).
             */
            totalTokens?: number;
            /** Format: int32 */
            latencyMs?: number;
            feedback?: components["schemas"]["FeedbackSummary"][];
            createdBy: components["schemas"]["User"];
            /**
             * Format: date-time
             * @description ISO-8601 date-time (restJson1 would otherwise default to epoch seconds).
             */
            createdAt: string;
        };
        /** @enum {string} */
        MessageKind: "customer" | "instruction";
        /** @enum {string} */
        MessageRole: "customer" | "instruction" | "assistant";
        /** @enum {string} */
        MessageStatus: "ok" | "failed";
        NotFoundErrorResponseContent: {
            message: string;
            resource?: string;
            id?: string;
        };
        PayloadTooLargeErrorResponseContent: {
            message: string;
            /** Format: int32 */
            maxBytes: number;
        };
        RateLimitedErrorResponseContent: {
            message: string;
            /** Format: int32 */
            retryAfterSeconds?: number;
        };
        RefreshTokenRequestContent: {
            refreshToken: string;
        };
        RefreshTokenResponseContent: {
            tokens: components["schemas"]["TokenSet"];
            user: components["schemas"]["User"];
        };
        RetrievedChunk: {
            chunkId: string;
            title?: string;
            /** Format: double */
            score: number;
        };
        RetryGuidelineVersionResponseContent: {
            version: components["schemas"]["GuidelineVersionSummary"];
        };
        SendMessageRequestContent: {
            kind: components["schemas"]["MessageKind"];
            content: string;
        };
        SendMessageResponseContent: {
            userMessage: components["schemas"]["Message"];
            assistantMessage: components["schemas"]["Message"];
        };
        SubmitFeedbackRequestContent: {
            rating: components["schemas"]["FeedbackRating"];
            whatWasWrong?: string;
            correctedAnswer?: string;
        };
        SubmitFeedbackResponseContent: {
            correction: components["schemas"]["Correction"];
        };
        /**
         * @description Short-lived access token (JWT, sent as Bearer) plus a long-lived, single-use refresh token.
         *     Reusing a rotated refresh token revokes the whole session family.
         */
        TokenSet: {
            accessToken: string;
            /**
             * Format: date-time
             * @description ISO-8601 date-time (restJson1 would otherwise default to epoch seconds).
             */
            accessExpiresAt: string;
            refreshToken: string;
            /**
             * Format: date-time
             * @description ISO-8601 date-time (restJson1 would otherwise default to epoch seconds).
             */
            refreshExpiresAt: string;
        };
        UnauthorizedErrorResponseContent: {
            message: string;
        };
        UnsupportedMediaTypeErrorResponseContent: {
            message: string;
            supported: string[];
        };
        UpdateCompanyRequestContent: {
            name?: string;
            description?: string;
        };
        UpdateCompanyResponseContent: {
            company: components["schemas"]["Company"];
        };
        UpdateCorrectionRequestContent: {
            active: boolean;
        };
        UpdateCorrectionResponseContent: {
            correction: components["schemas"]["Correction"];
        };
        /** @description Raw uploaded guideline file bytes. */
        UploadGuidelinesInputPayload: Blob;
        UploadGuidelinesResponseContent: {
            version: components["schemas"]["GuidelineVersionSummary"];
        };
        UsedCorrection: {
            correctionId: string;
            /** Format: double */
            score: number;
        };
        User: {
            id: string;
            username: string;
            displayName: string;
        };
        /** @description Describes one specific validation failure for an input member. */
        ValidationExceptionField: {
            /** @description A JSONPointer expression to the structure member whose value failed to satisfy the modeled constraints. */
            path: string;
            /** @description A detailed description of the validation failure. */
            message: string;
        };
        /**
         * @description A standard error for input validation failures.
         *     This should be thrown by services when a member of the input structure
         *     falls outside of the modeled or documented constraints.
         */
        ValidationExceptionResponseContent: {
            /** @description A summary of the validation failure. */
            message: string;
            /**
             * @description A list of specific failures encountered while validating the input.
             *     A member can appear in this list more than once if it failed to satisfy multiple constraints.
             */
            fieldList?: components["schemas"]["ValidationExceptionField"][];
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    Login: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LoginRequestContent"];
            };
        };
        responses: {
            /** @description Login 200 response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LoginResponseContent"];
                };
            };
            /** @description ValidationException 400 response */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description UnauthorizedError 401 response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description RateLimitedError 429 response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description InternalServerError 500 response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
        };
    };
    Logout: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LogoutRequestContent"];
            };
        };
        responses: {
            /** @description Logout 200 response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LogoutResponseContent"];
                };
            };
            /** @description ValidationException 400 response */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description UnauthorizedError 401 response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description RateLimitedError 429 response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description InternalServerError 500 response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
        };
    };
    GetCurrentUser: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description GetCurrentUser 200 response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GetCurrentUserResponseContent"];
                };
            };
            /** @description ValidationException 400 response */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description UnauthorizedError 401 response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description RateLimitedError 429 response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description InternalServerError 500 response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
        };
    };
    RefreshToken: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RefreshTokenRequestContent"];
            };
        };
        responses: {
            /** @description RefreshToken 200 response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RefreshTokenResponseContent"];
                };
            };
            /** @description ValidationException 400 response */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description UnauthorizedError 401 response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description RateLimitedError 429 response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description InternalServerError 500 response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
        };
    };
    ListCompanies: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description ListCompanies 200 response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ListCompaniesResponseContent"];
                };
            };
            /** @description ValidationException 400 response */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description UnauthorizedError 401 response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description RateLimitedError 429 response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description InternalServerError 500 response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
        };
    };
    CreateCompany: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateCompanyRequestContent"];
            };
        };
        responses: {
            /** @description CreateCompany 201 response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CreateCompanyResponseContent"];
                };
            };
            /** @description ValidationException 400 response */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description UnauthorizedError 401 response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description ConflictError 409 response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConflictErrorResponseContent"];
                };
            };
            /** @description RateLimitedError 429 response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description InternalServerError 500 response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
        };
    };
    GetCompany: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                companyId: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description GetCompany 200 response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GetCompanyResponseContent"];
                };
            };
            /** @description ValidationException 400 response */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description UnauthorizedError 401 response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description NotFoundError 404 response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description RateLimitedError 429 response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description InternalServerError 500 response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
        };
    };
    UpdateCompany: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                companyId: string;
            };
            cookie?: never;
        };
        requestBody?: {
            content: {
                "application/json": components["schemas"]["UpdateCompanyRequestContent"];
            };
        };
        responses: {
            /** @description UpdateCompany 200 response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UpdateCompanyResponseContent"];
                };
            };
            /** @description ValidationException 400 response */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description UnauthorizedError 401 response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description NotFoundError 404 response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description ConflictError 409 response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConflictErrorResponseContent"];
                };
            };
            /** @description RateLimitedError 429 response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description InternalServerError 500 response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
        };
    };
    ListCorrections: {
        parameters: {
            query?: {
                includeInactive?: boolean;
            };
            header?: never;
            path: {
                companyId: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description ListCorrections 200 response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ListCorrectionsResponseContent"];
                };
            };
            /** @description ValidationException 400 response */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description UnauthorizedError 401 response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description NotFoundError 404 response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description RateLimitedError 429 response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description InternalServerError 500 response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
        };
    };
    GetActiveGuidelines: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                companyId: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description GetActiveGuidelines 200 response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GetActiveGuidelinesResponseContent"];
                };
            };
            /** @description ValidationException 400 response */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description UnauthorizedError 401 response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description NotFoundError 404 response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description GuidelinesNotReadyError 409 response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GuidelinesNotReadyErrorResponseContent"];
                };
            };
            /** @description RateLimitedError 429 response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description InternalServerError 500 response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
        };
    };
    UploadGuidelines: {
        parameters: {
            query?: never;
            header: {
                /**
                 * @description Id of the latest guideline version the client displayed. If a newer
                 *     version exists the upload is rejected with GuidelinesConflictError.
                 */
                "X-Expected-Version"?: string;
                /** @description Original MIME type as reported by the browser, if known. */
                "X-File-Content-Type"?: string;
                /** @description Original file name (extension is used to pick the parser). */
                "X-Filename": string;
            };
            path: {
                companyId: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/octet-stream": components["schemas"]["UploadGuidelinesInputPayload"];
            };
        };
        responses: {
            /** @description UploadGuidelines 202 response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UploadGuidelinesResponseContent"];
                };
            };
            /** @description ValidationException 400 response */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description UnauthorizedError 401 response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description NotFoundError 404 response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description GuidelinesConflictError 409 response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GuidelinesConflictErrorResponseContent"];
                };
            };
            /** @description PayloadTooLargeError 413 response */
            413: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PayloadTooLargeErrorResponseContent"];
                };
            };
            /** @description UnsupportedMediaTypeError 415 response */
            415: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnsupportedMediaTypeErrorResponseContent"];
                };
            };
            /** @description RateLimitedError 429 response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description InternalServerError 500 response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
        };
    };
    ListGuidelineVersions: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                companyId: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description ListGuidelineVersions 200 response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ListGuidelineVersionsResponseContent"];
                };
            };
            /** @description ValidationException 400 response */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description UnauthorizedError 401 response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description NotFoundError 404 response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description RateLimitedError 429 response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description InternalServerError 500 response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
        };
    };
    ListConversations: {
        parameters: {
            query?: {
                companyId?: string;
                coverage?: components["schemas"]["Coverage"];
                /** @description Cursor for paginated list operations (opaque to clients). */
                cursor?: string;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description ListConversations 200 response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ListConversationsResponseContent"];
                };
            };
            /** @description ValidationException 400 response */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description UnauthorizedError 401 response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description RateLimitedError 429 response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description InternalServerError 500 response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
        };
    };
    CreateConversation: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateConversationRequestContent"];
            };
        };
        responses: {
            /** @description CreateConversation 201 response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CreateConversationResponseContent"];
                };
            };
            /** @description ValidationException 400 response */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description UnauthorizedError 401 response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description NotFoundError 404 response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description GuidelinesNotReadyError 409 response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GuidelinesNotReadyErrorResponseContent"];
                };
            };
            /** @description RateLimitedError 429 response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description InternalServerError 500 response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
        };
    };
    GetConversation: {
        parameters: {
            query?: {
                /** @description Load messages older than this cursor (from a previous page's `olderCursor`). */
                before?: string;
                /** @description Messages per page (default 50). */
                limit?: number;
            };
            header?: never;
            path: {
                conversationId: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description GetConversation 200 response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GetConversationResponseContent"];
                };
            };
            /** @description ValidationException 400 response */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description UnauthorizedError 401 response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description NotFoundError 404 response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description RateLimitedError 429 response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description InternalServerError 500 response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
        };
    };
    SendMessage: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                conversationId: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SendMessageRequestContent"];
            };
        };
        responses: {
            /** @description SendMessage 201 response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SendMessageResponseContent"];
                };
            };
            /** @description ValidationException 400 response */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description UnauthorizedError 401 response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description NotFoundError 404 response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description GuidelinesNotReadyError 409 response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GuidelinesNotReadyErrorResponseContent"];
                };
            };
            /** @description RateLimitedError 429 response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description InternalServerError 500 response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
            /** @description AiProviderError 502 response */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AiProviderErrorResponseContent"];
                };
            };
        };
    };
    UpdateCorrection: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                correctionId: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UpdateCorrectionRequestContent"];
            };
        };
        responses: {
            /** @description UpdateCorrection 200 response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UpdateCorrectionResponseContent"];
                };
            };
            /** @description ValidationException 400 response */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description UnauthorizedError 401 response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description NotFoundError 404 response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description RateLimitedError 429 response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description InternalServerError 500 response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
        };
    };
    GetGuidelineVersion: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                versionId: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description GetGuidelineVersion 200 response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GetGuidelineVersionResponseContent"];
                };
            };
            /** @description ValidationException 400 response */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description UnauthorizedError 401 response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description NotFoundError 404 response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description RateLimitedError 429 response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description InternalServerError 500 response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
        };
    };
    ActivateGuidelineVersion: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                versionId: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description ActivateGuidelineVersion 200 response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ActivateGuidelineVersionResponseContent"];
                };
            };
            /** @description ValidationException 400 response */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description UnauthorizedError 401 response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description NotFoundError 404 response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description ConflictError 409 response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConflictErrorResponseContent"];
                };
            };
            /** @description RateLimitedError 429 response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description InternalServerError 500 response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
        };
    };
    RetryGuidelineVersion: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                versionId: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description RetryGuidelineVersion 200 response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RetryGuidelineVersionResponseContent"];
                };
            };
            /** @description ValidationException 400 response */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description UnauthorizedError 401 response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description NotFoundError 404 response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description ConflictError 409 response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConflictErrorResponseContent"];
                };
            };
            /** @description RateLimitedError 429 response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description InternalServerError 500 response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
        };
    };
    Health: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Health 200 response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HealthResponseContent"];
                };
            };
            /** @description ValidationException 400 response */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description UnauthorizedError 401 response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description RateLimitedError 429 response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description InternalServerError 500 response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
        };
    };
    SubmitFeedback: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                messageId: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SubmitFeedbackRequestContent"];
            };
        };
        responses: {
            /** @description SubmitFeedback 200 response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubmitFeedbackResponseContent"];
                };
            };
            /** @description ValidationException 400 response */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description UnauthorizedError 401 response */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description NotFoundError 404 response */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description ConflictError 409 response */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConflictErrorResponseContent"];
                };
            };
            /** @description RateLimitedError 429 response */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description InternalServerError 500 response */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
        };
    };
}
