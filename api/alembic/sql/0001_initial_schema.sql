CREATE TYPE "public"."coverage" AS ENUM('covered', 'partial', 'not_covered');--> statement-breakpoint
CREATE TYPE "public"."feedback_rating" AS ENUM('up', 'down');--> statement-breakpoint
CREATE TYPE "public"."guideline_status" AS ENUM('queued', 'parsing', 'chunking', 'embedding', 'ready', 'failed', 'superseded');--> statement-breakpoint
CREATE TYPE "public"."message_role" AS ENUM('customer', 'instruction', 'assistant');--> statement-breakpoint
CREATE TYPE "public"."message_status" AS ENUM('ok', 'failed');--> statement-breakpoint
CREATE TABLE "companies" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"name" text NOT NULL,
	"description" text,
	"active_guideline_version_id" uuid,
	"created_by" uuid NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "conversations" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"company_id" uuid NOT NULL,
	"title" text DEFAULT '' NOT NULL,
	"history_summary" text,
	"history_summary_upto" uuid,
	"created_by" uuid NOT NULL,
	"last_message_at" timestamp with time zone DEFAULT now() NOT NULL,
	"last_coverage" "coverage",
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "feedback" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"message_id" uuid NOT NULL,
	"conversation_id" uuid NOT NULL,
	"company_id" uuid NOT NULL,
	"user_id" uuid NOT NULL,
	"rating" "feedback_rating" NOT NULL,
	"what_was_wrong" text,
	"corrected_answer" text,
	"query_text" text NOT NULL,
	"query_embedding" vector(768),
	"guideline_version_id" uuid NOT NULL,
	"active" boolean DEFAULT true NOT NULL,
	"score" double precision,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "guideline_chunks" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"version_id" uuid NOT NULL,
	"company_id" uuid NOT NULL,
	"ordinal" integer NOT NULL,
	"title" text,
	"content" text NOT NULL,
	"token_count" integer NOT NULL,
	"embedding" vector(768),
	"search_vector" "tsvector" GENERATED ALWAYS AS (to_tsvector('english', coalesce(title, '') || ' ' || content)) STORED
);
--> statement-breakpoint
CREATE TABLE "guideline_versions" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"seq" bigserial NOT NULL,
	"company_id" uuid NOT NULL,
	"filename" text NOT NULL,
	"content_type" text NOT NULL,
	"size_bytes" integer NOT NULL,
	"sha256" text NOT NULL,
	"file_bytes" "bytea" NOT NULL,
	"raw_text" text,
	"status" "guideline_status" DEFAULT 'queued' NOT NULL,
	"chunks_total" integer DEFAULT 0 NOT NULL,
	"chunks_embedded" integer DEFAULT 0 NOT NULL,
	"error" text,
	"job_id" text,
	"superseded_by" uuid,
	"created_by" uuid NOT NULL,
	"ready_at" timestamp with time zone,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "guideline_versions_seq_unique" UNIQUE("seq")
);
--> statement-breakpoint
CREATE TABLE "messages" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"conversation_id" uuid NOT NULL,
	"role" "message_role" NOT NULL,
	"content" text NOT NULL,
	"status" "message_status" DEFAULT 'ok' NOT NULL,
	"error" text,
	"guidance" jsonb,
	"coverage" "coverage",
	"retrieval" jsonb,
	"corrections_used" jsonb,
	"guideline_version_id" uuid,
	"model" text,
	"prompt_tokens" integer,
	"completion_tokens" integer,
	"latency_ms" integer,
	"trace_id" text,
	"created_by" uuid NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "refresh_tokens" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"family_id" uuid NOT NULL,
	"token_hash" text NOT NULL,
	"expires_at" timestamp with time zone NOT NULL,
	"revoked_at" timestamp with time zone,
	"replaced_by" uuid,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "refresh_tokens_token_hash_unique" UNIQUE("token_hash")
);
--> statement-breakpoint
CREATE TABLE "users" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"username" text NOT NULL,
	"password_hash" text NOT NULL,
	"display_name" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "users_username_unique" UNIQUE("username")
);
--> statement-breakpoint
ALTER TABLE "companies" ADD CONSTRAINT "companies_active_guideline_version_id_guideline_versions_id_fk" FOREIGN KEY ("active_guideline_version_id") REFERENCES "public"."guideline_versions"("id") ON DELETE set null ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "companies" ADD CONSTRAINT "companies_created_by_users_id_fk" FOREIGN KEY ("created_by") REFERENCES "public"."users"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "conversations" ADD CONSTRAINT "conversations_company_id_companies_id_fk" FOREIGN KEY ("company_id") REFERENCES "public"."companies"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "conversations" ADD CONSTRAINT "conversations_created_by_users_id_fk" FOREIGN KEY ("created_by") REFERENCES "public"."users"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "feedback" ADD CONSTRAINT "feedback_message_id_messages_id_fk" FOREIGN KEY ("message_id") REFERENCES "public"."messages"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "feedback" ADD CONSTRAINT "feedback_conversation_id_conversations_id_fk" FOREIGN KEY ("conversation_id") REFERENCES "public"."conversations"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "feedback" ADD CONSTRAINT "feedback_company_id_companies_id_fk" FOREIGN KEY ("company_id") REFERENCES "public"."companies"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "feedback" ADD CONSTRAINT "feedback_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "guideline_chunks" ADD CONSTRAINT "guideline_chunks_version_id_guideline_versions_id_fk" FOREIGN KEY ("version_id") REFERENCES "public"."guideline_versions"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "guideline_chunks" ADD CONSTRAINT "guideline_chunks_company_id_companies_id_fk" FOREIGN KEY ("company_id") REFERENCES "public"."companies"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "guideline_versions" ADD CONSTRAINT "guideline_versions_company_id_companies_id_fk" FOREIGN KEY ("company_id") REFERENCES "public"."companies"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "guideline_versions" ADD CONSTRAINT "guideline_versions_created_by_users_id_fk" FOREIGN KEY ("created_by") REFERENCES "public"."users"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "messages" ADD CONSTRAINT "messages_conversation_id_conversations_id_fk" FOREIGN KEY ("conversation_id") REFERENCES "public"."conversations"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "messages" ADD CONSTRAINT "messages_created_by_users_id_fk" FOREIGN KEY ("created_by") REFERENCES "public"."users"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "refresh_tokens" ADD CONSTRAINT "refresh_tokens_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
CREATE UNIQUE INDEX "companies_name_lower_idx" ON "companies" USING btree (lower("name"));--> statement-breakpoint
CREATE INDEX "conversations_company_last_idx" ON "conversations" USING btree ("company_id","last_message_at");--> statement-breakpoint
CREATE INDEX "conversations_last_idx" ON "conversations" USING btree ("last_message_at");--> statement-breakpoint
CREATE INDEX "conversations_coverage_last_idx" ON "conversations" USING btree ("last_coverage","last_message_at");--> statement-breakpoint
CREATE UNIQUE INDEX "feedback_message_user_idx" ON "feedback" USING btree ("message_id","user_id");--> statement-breakpoint
CREATE INDEX "feedback_company_active_idx" ON "feedback" USING btree ("company_id","active");--> statement-breakpoint
CREATE INDEX "feedback_embedding_idx" ON "feedback" USING hnsw ("query_embedding" vector_cosine_ops);--> statement-breakpoint
CREATE INDEX "guideline_chunks_version_idx" ON "guideline_chunks" USING btree ("version_id","ordinal");--> statement-breakpoint
CREATE INDEX "guideline_chunks_embedding_idx" ON "guideline_chunks" USING hnsw ("embedding" vector_cosine_ops);--> statement-breakpoint
CREATE INDEX "guideline_chunks_search_idx" ON "guideline_chunks" USING gin ("search_vector");--> statement-breakpoint
CREATE INDEX "guideline_versions_company_seq_idx" ON "guideline_versions" USING btree ("company_id","seq");--> statement-breakpoint
CREATE INDEX "messages_conversation_created_idx" ON "messages" USING btree ("conversation_id","created_at");--> statement-breakpoint
CREATE INDEX "refresh_tokens_family_idx" ON "refresh_tokens" USING btree ("family_id");--> statement-breakpoint
CREATE INDEX "refresh_tokens_user_idx" ON "refresh_tokens" USING btree ("user_id");