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
        /** Login */
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
        /** Logout */
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
        /** Me */
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
        /** Refresh */
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
        /** List Companies */
        get: operations["ListCompanies"];
        put?: never;
        /** Create Company */
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
        /** Get Company */
        get: operations["GetCompany"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Company */
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
        /** List Corrections */
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
        /** Get Active Guidelines */
        get: operations["GetActiveGuidelines"];
        /** Upload Guidelines */
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
        /** List Guideline Versions */
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
        /** List Conversations */
        get: operations["ListConversations"];
        put?: never;
        /** Create Conversation */
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
        /** Get Conversation */
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
        /** Send Message */
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
        /** Update Correction */
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
        /** Get Guideline Version */
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
        /** Activate Guideline Version */
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
        /** Retry Guideline Version */
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
        /** Health */
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
        /** Submit Feedback */
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
        /** ActivateGuidelineVersionResponseContent */
        ActivateGuidelineVersionResponseContent: {
            version: components["schemas"]["GuidelineVersionSummary"];
        };
        /**
         * AiProviderErrorResponseContent
         * @description The AI provider failed or timed out. Safe to retry.
         */
        AiProviderErrorResponseContent: {
            /** Message */
            message: string;
            /** Provider */
            provider?: string;
        };
        /**
         * AssistantGuidance
         * @description Structured guidance produced by the assistant for the agent.
         */
        AssistantGuidance: {
            coverage: components["schemas"]["Coverage"];
            /**
             * Recommendedreply
             * @description Customer-facing draft; placeholders like [Name] are left for the agent.
             */
            recommendedReply: string;
            /**
             * Handlingsteps
             * @description Internal steps for the agent, in order.
             */
            handlingSteps: string[];
            /**
             * Clarifications
             * @description Questions the customer must answer before the case can be resolved
             *     (preferences, missing details). Optional for older messages.
             */
            clarifications?: string[];
            /**
             * Agentdecisions
             * @description Decisions the guidelines leave to the agent's judgement (never questions for the customer).
             */
            agentDecisions: string[];
            escalation: components["schemas"]["Escalation"];
            /** Citations */
            citations: components["schemas"]["Citation"][];
            /** Notes */
            notes?: string;
        };
        /** Citation */
        Citation: {
            /** Chunkid */
            chunkId: string;
            /** Title */
            title?: string;
        };
        /** Company */
        Company: {
            /** Id */
            id: string;
            /** Name */
            name: string;
            /** Description */
            description?: string;
            /** Activeguidelines */
            activeGuidelines?: components["schemas"]["GuidelineVersionSummary"];
            /** Latestguidelines */
            latestGuidelines?: components["schemas"]["GuidelineVersionSummary"];
            /** Conversationcount */
            conversationCount: number;
            /**
             * Createdat
             * Format: date-time
             */
            createdAt: string;
            /**
             * Updatedat
             * Format: date-time
             */
            updatedAt: string;
        };
        /**
         * ConflictErrorResponseContent
         * @description Generic conflict (e.g. duplicate company name).
         */
        ConflictErrorResponseContent: {
            /** Message */
            message: string;
        };
        /** Conversation */
        Conversation: {
            summary: components["schemas"]["ConversationSummary"];
            /** Messages */
            messages: components["schemas"]["Message"][];
        };
        /** ConversationSummary */
        ConversationSummary: {
            /** Id */
            id: string;
            /** Companyid */
            companyId: string;
            /** Companyname */
            companyName: string;
            /** Title */
            title: string;
            /** Messagecount */
            messageCount: number;
            /** Lastcoverage */
            lastCoverage?: components["schemas"]["Coverage"];
            createdBy: components["schemas"]["User"];
            /**
             * Createdat
             * Format: date-time
             */
            createdAt: string;
            /**
             * Lastmessageat
             * Format: date-time
             */
            lastMessageAt: string;
        };
        /**
         * Correction
         * @description A stored piece of feedback, used as a few-shot correction for future answers.
         */
        Correction: {
            /** Id */
            id: string;
            /** Companyid */
            companyId: string;
            /** Conversationid */
            conversationId: string;
            /** Messageid */
            messageId: string;
            rating: components["schemas"]["FeedbackRating"];
            /**
             * Querytext
             * @description The customer message that led to the flagged answer.
             */
            queryText: string;
            /** Whatwaswrong */
            whatWasWrong?: string;
            /** Correctedanswer */
            correctedAnswer?: string;
            /** Guidelineversionid */
            guidelineVersionId: string;
            /**
             * Active
             * @description Inactive corrections are not retrieved (e.g. tied to replaced guidelines).
             */
            active: boolean;
            user: components["schemas"]["User"];
            /**
             * Createdat
             * Format: date-time
             */
            createdAt: string;
        };
        /**
         * Coverage
         * @enum {string}
         */
        Coverage: "covered" | "partial" | "not_covered";
        /** CreateCompanyRequestContent */
        CreateCompanyRequestContent: {
            /** Name */
            name: string;
            /** Description */
            description?: string;
        };
        /** CreateCompanyResponseContent */
        CreateCompanyResponseContent: {
            company: components["schemas"]["Company"];
        };
        /** CreateConversationRequestContent */
        CreateConversationRequestContent: {
            /** Companyid */
            companyId: string;
        };
        /** CreateConversationResponseContent */
        CreateConversationResponseContent: {
            conversation: components["schemas"]["Conversation"];
        };
        /** Escalation */
        Escalation: {
            /** Recommended */
            recommended: boolean;
            /** To */
            to?: string;
            /** Reason */
            reason?: string;
        };
        /**
         * FeedbackRating
         * @enum {string}
         */
        FeedbackRating: "up" | "down";
        /**
         * FeedbackSummary
         * @description Feedback the current or another user left on an assistant message.
         */
        FeedbackSummary: {
            /** Id */
            id: string;
            rating: components["schemas"]["FeedbackRating"];
            /** Whatwaswrong */
            whatWasWrong?: string;
            /** Correctedanswer */
            correctedAnswer?: string;
            user: components["schemas"]["User"];
            /**
             * Createdat
             * Format: date-time
             */
            createdAt: string;
        };
        /** GetActiveGuidelinesResponseContent */
        GetActiveGuidelinesResponseContent: {
            version: components["schemas"]["GuidelineVersionSummary"];
            /** Text */
            text: string;
            /** Chunks */
            chunks: components["schemas"]["GuidelineChunk"][];
        };
        /** GetCompanyResponseContent */
        GetCompanyResponseContent: {
            company: components["schemas"]["Company"];
        };
        /** GetConversationResponseContent */
        GetConversationResponseContent: {
            conversation: components["schemas"]["Conversation"];
            /**
             * Oldercursor
             * @description Present when older messages exist; pass it as `before` to load them.
             */
            olderCursor?: string;
        };
        /** GetCurrentUserResponseContent */
        GetCurrentUserResponseContent: {
            user: components["schemas"]["User"];
        };
        /** GetGuidelineVersionResponseContent */
        GetGuidelineVersionResponseContent: {
            version: components["schemas"]["GuidelineVersionSummary"];
        };
        /** GuidelineChunk */
        GuidelineChunk: {
            /** Id */
            id: string;
            /** Ordinal */
            ordinal: number;
            /** Title */
            title?: string;
            /** Content */
            content: string;
            /** Tokencount */
            tokenCount: number;
        };
        /**
         * GuidelineStatus
         * @enum {string}
         */
        GuidelineStatus: "queued" | "parsing" | "chunking" | "embedding" | "ready" | "failed" | "superseded";
        /** GuidelineVersionSummary */
        GuidelineVersionSummary: {
            /** Id */
            id: string;
            /** Companyid */
            companyId: string;
            /** Filename */
            filename: string;
            /** Contenttype */
            contentType: string;
            /** Sizebytes */
            sizeBytes: number;
            status: components["schemas"]["GuidelineStatus"];
            /** Chunkstotal */
            chunksTotal: number;
            /** Chunksembedded */
            chunksEmbedded: number;
            /** Error */
            error?: string;
            /** Isactive */
            isActive: boolean;
            uploadedBy: components["schemas"]["User"];
            /**
             * Createdat
             * Format: date-time
             */
            createdAt: string;
            /**
             * Updatedat
             * Format: date-time
             */
            updatedAt: string;
            /**
             * Readyat
             * Format: date-time
             */
            readyAt?: string;
            /** Supersededby */
            supersededBy?: string;
        };
        /**
         * GuidelinesConflictErrorResponseContent
         * @description Another user uploaded guidelines after the client loaded the page.
         */
        GuidelinesConflictErrorResponseContent: {
            /** Message */
            message: string;
            /** Latestversionid */
            latestVersionId: string;
            uploadedBy: components["schemas"]["User"];
            /**
             * Uploadedat
             * Format: date-time
             */
            uploadedAt: string;
        };
        /** GuidelinesNotReadyErrorResponseContent */
        GuidelinesNotReadyErrorResponseContent: {
            /** Message */
            message: string;
            /** Companyid */
            companyId: string;
            /** Lateststatus */
            latestStatus?: components["schemas"]["GuidelineStatus"];
        };
        /** HealthResponseContent */
        HealthResponseContent: {
            /** Status */
            status: string;
            /** Service */
            service: string;
            /**
             * Time
             * Format: date-time
             */
            time: string;
        };
        /** InternalServerErrorResponseContent */
        InternalServerErrorResponseContent: {
            /** Message */
            message: string;
            /** Requestid */
            requestId?: string;
        };
        /** ListCompaniesResponseContent */
        ListCompaniesResponseContent: {
            /** Items */
            items: components["schemas"]["Company"][];
        };
        /** ListConversationsResponseContent */
        ListConversationsResponseContent: {
            /** Items */
            items: components["schemas"]["ConversationSummary"][];
            /**
             * Nextcursor
             * @description Cursor for paginated list operations (opaque to clients).
             */
            nextCursor?: string;
        };
        /** ListCorrectionsResponseContent */
        ListCorrectionsResponseContent: {
            /** Items */
            items: components["schemas"]["Correction"][];
        };
        /** ListGuidelineVersionsResponseContent */
        ListGuidelineVersionsResponseContent: {
            /** Items */
            items: components["schemas"]["GuidelineVersionSummary"][];
        };
        /** LoginRequestContent */
        LoginRequestContent: {
            /** Username */
            username: string;
            /** Password */
            password: string;
        };
        /** LoginResponseContent */
        LoginResponseContent: {
            tokens: components["schemas"]["TokenSet"];
            user: components["schemas"]["User"];
        };
        /** LogoutRequestContent */
        LogoutRequestContent: {
            /** Refreshtoken */
            refreshToken: string;
        };
        /** LogoutResponseContent */
        LogoutResponseContent: {
            /** Revoked */
            revoked: boolean;
        };
        /** Message */
        Message: {
            /** Id */
            id: string;
            /** Conversationid */
            conversationId: string;
            role: components["schemas"]["MessageRole"];
            /**
             * Content
             * @description Raw text for customer/instruction messages; the recommended reply for
             *     assistant messages (full structure in `guidance`).
             */
            content: string;
            status: components["schemas"]["MessageStatus"];
            /** Error */
            error?: string;
            /** Guidance */
            guidance?: components["schemas"]["AssistantGuidance"];
            /** Retrieval */
            retrieval?: components["schemas"]["RetrievedChunk"][];
            /** Correctionsused */
            correctionsUsed?: components["schemas"]["UsedCorrection"][];
            /** Guidelineversionid */
            guidelineVersionId?: string;
            /** Model */
            model?: string;
            /**
             * Prompttokens
             * @description Tokens in the prompt (system instruction, history, retrieved context).
             */
            promptTokens?: number;
            /**
             * Completiontokens
             * @description Visible answer tokens, excluding the model's reasoning.
             */
            completionTokens?: number;
            /**
             * Thinkingtokens
             * @description Reasoning ("thinking") tokens; billed as output but not part of the answer.
             */
            thinkingTokens?: number;
            /**
             * Totaltokens
             * @description Total tokens billed for the call as reported by the provider (prompt + thinking + answer).
             */
            totalTokens?: number;
            /** Latencyms */
            latencyMs?: number;
            /** Feedback */
            feedback?: components["schemas"]["FeedbackSummary"][];
            createdBy: components["schemas"]["User"];
            /**
             * Createdat
             * Format: date-time
             */
            createdAt: string;
        };
        /**
         * MessageKind
         * @enum {string}
         */
        MessageKind: "customer" | "instruction";
        /**
         * MessageRole
         * @enum {string}
         */
        MessageRole: "customer" | "instruction" | "assistant";
        /**
         * MessageStatus
         * @enum {string}
         */
        MessageStatus: "ok" | "failed";
        /** NotFoundErrorResponseContent */
        NotFoundErrorResponseContent: {
            /** Message */
            message: string;
            /** Resource */
            resource?: string;
            /** Id */
            id?: string;
        };
        /** PayloadTooLargeErrorResponseContent */
        PayloadTooLargeErrorResponseContent: {
            /** Message */
            message: string;
            /** Maxbytes */
            maxBytes: number;
        };
        /** RateLimitedErrorResponseContent */
        RateLimitedErrorResponseContent: {
            /** Message */
            message: string;
            /** Retryafterseconds */
            retryAfterSeconds?: number;
        };
        /** RefreshTokenRequestContent */
        RefreshTokenRequestContent: {
            /** Refreshtoken */
            refreshToken: string;
        };
        /** RefreshTokenResponseContent */
        RefreshTokenResponseContent: {
            tokens: components["schemas"]["TokenSet"];
            user: components["schemas"]["User"];
        };
        /** RetrievedChunk */
        RetrievedChunk: {
            /** Chunkid */
            chunkId: string;
            /** Title */
            title?: string;
            /** Score */
            score: number;
        };
        /** RetryGuidelineVersionResponseContent */
        RetryGuidelineVersionResponseContent: {
            version: components["schemas"]["GuidelineVersionSummary"];
        };
        /** SendMessageRequestContent */
        SendMessageRequestContent: {
            kind: components["schemas"]["MessageKind"];
            /** Content */
            content: string;
        };
        /** SendMessageResponseContent */
        SendMessageResponseContent: {
            userMessage: components["schemas"]["Message"];
            assistantMessage: components["schemas"]["Message"];
        };
        /** SubmitFeedbackRequestContent */
        SubmitFeedbackRequestContent: {
            rating: components["schemas"]["FeedbackRating"];
            /** Whatwaswrong */
            whatWasWrong?: string;
            /** Correctedanswer */
            correctedAnswer?: string;
        };
        /** SubmitFeedbackResponseContent */
        SubmitFeedbackResponseContent: {
            correction: components["schemas"]["Correction"];
        };
        /**
         * TokenSet
         * @description Short-lived access token (JWT, sent as Bearer) plus a long-lived, single-use refresh token.
         *     Reusing a rotated refresh token revokes the whole session family.
         */
        TokenSet: {
            /** Accesstoken */
            accessToken: string;
            /**
             * Accessexpiresat
             * Format: date-time
             */
            accessExpiresAt: string;
            /** Refreshtoken */
            refreshToken: string;
            /**
             * Refreshexpiresat
             * Format: date-time
             */
            refreshExpiresAt: string;
        };
        /** UnauthorizedErrorResponseContent */
        UnauthorizedErrorResponseContent: {
            /** Message */
            message: string;
        };
        /** UnsupportedMediaTypeErrorResponseContent */
        UnsupportedMediaTypeErrorResponseContent: {
            /** Message */
            message: string;
            /** Supported */
            supported: string[];
        };
        /** UpdateCompanyRequestContent */
        UpdateCompanyRequestContent: {
            /** Name */
            name?: string;
            /** Description */
            description?: string;
        };
        /** UpdateCompanyResponseContent */
        UpdateCompanyResponseContent: {
            company: components["schemas"]["Company"];
        };
        /** UpdateCorrectionRequestContent */
        UpdateCorrectionRequestContent: {
            /** Active */
            active: boolean;
        };
        /** UpdateCorrectionResponseContent */
        UpdateCorrectionResponseContent: {
            correction: components["schemas"]["Correction"];
        };
        /** @description Raw uploaded guideline file bytes. */
        UploadGuidelinesInputPayload: Blob;
        /** UploadGuidelinesResponseContent */
        UploadGuidelinesResponseContent: {
            version: components["schemas"]["GuidelineVersionSummary"];
        };
        /** UsedCorrection */
        UsedCorrection: {
            /** Correctionid */
            correctionId: string;
            /** Score */
            score: number;
        };
        /** User */
        User: {
            /** Id */
            id: string;
            /** Username */
            username: string;
            /** Displayname */
            displayName: string;
        };
        /**
         * ValidationExceptionField
         * @description Describes one specific validation failure for an input member.
         */
        ValidationExceptionField: {
            /**
             * Path
             * @description A JSONPointer expression to the structure member whose value failed to satisfy the modeled constraints.
             */
            path: string;
            /**
             * Message
             * @description A detailed description of the validation failure.
             */
            message: string;
        };
        /**
         * ValidationExceptionResponseContent
         * @description A standard error for input validation failures.
         */
        ValidationExceptionResponseContent: {
            /**
             * Message
             * @description A summary of the validation failure.
             */
            message: string;
            /**
             * Fieldlist
             * @description A list of specific failures encountered while validating the input.
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
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LoginResponseContent"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description Internal Server Error */
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
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LogoutResponseContent"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description Internal Server Error */
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
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GetCurrentUserResponseContent"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description Internal Server Error */
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
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RefreshTokenResponseContent"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description Internal Server Error */
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
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ListCompaniesResponseContent"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description Internal Server Error */
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
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CreateCompanyResponseContent"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConflictErrorResponseContent"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description Internal Server Error */
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
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GetCompanyResponseContent"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description Internal Server Error */
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
        requestBody: {
            content: {
                "application/json": components["schemas"]["UpdateCompanyRequestContent"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UpdateCompanyResponseContent"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConflictErrorResponseContent"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description Internal Server Error */
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
                includeInactive?: boolean | null;
            };
            header?: never;
            path: {
                companyId: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ListCorrectionsResponseContent"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description Internal Server Error */
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
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GetActiveGuidelinesResponseContent"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GuidelinesNotReadyErrorResponseContent"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description Internal Server Error */
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
                /** @description Original file name (extension is used to pick the parser). */
                "X-Filename": string;
                /** @description Original MIME type as reported by the browser, if known. */
                "X-File-Content-Type"?: string | null;
                /**
                 * @description Id of the latest guideline version the client displayed. If a newer
                 *     version exists the upload is rejected with GuidelinesConflictError.
                 */
                "X-Expected-Version"?: string | null;
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
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UploadGuidelinesResponseContent"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GuidelinesConflictErrorResponseContent"];
                };
            };
            /** @description Request Entity Too Large */
            413: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PayloadTooLargeErrorResponseContent"];
                };
            };
            /** @description Unsupported Media Type */
            415: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnsupportedMediaTypeErrorResponseContent"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description Internal Server Error */
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
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ListGuidelineVersionsResponseContent"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description Internal Server Error */
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
                companyId?: string | null;
                coverage?: components["schemas"]["Coverage"] | null;
                /** @description Cursor for paginated list operations (opaque to clients). */
                cursor?: string | null;
                limit?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ListConversationsResponseContent"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description Internal Server Error */
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
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CreateConversationResponseContent"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GuidelinesNotReadyErrorResponseContent"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description Internal Server Error */
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
                before?: string | null;
                /** @description Messages per page (default 50). */
                limit?: number | null;
            };
            header?: never;
            path: {
                conversationId: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GetConversationResponseContent"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description Internal Server Error */
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
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SendMessageResponseContent"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GuidelinesNotReadyErrorResponseContent"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description Internal Server Error */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InternalServerErrorResponseContent"];
                };
            };
            /** @description Bad Gateway */
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
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UpdateCorrectionResponseContent"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description Internal Server Error */
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
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GetGuidelineVersionResponseContent"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description Internal Server Error */
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
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ActivateGuidelineVersionResponseContent"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConflictErrorResponseContent"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description Internal Server Error */
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
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RetryGuidelineVersionResponseContent"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConflictErrorResponseContent"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description Internal Server Error */
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
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HealthResponseContent"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description Internal Server Error */
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
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubmitFeedbackResponseContent"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ValidationExceptionResponseContent"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UnauthorizedErrorResponseContent"];
                };
            };
            /** @description Not Found */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NotFoundErrorResponseContent"];
                };
            };
            /** @description Conflict */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConflictErrorResponseContent"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateLimitedErrorResponseContent"];
                };
            };
            /** @description Internal Server Error */
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
