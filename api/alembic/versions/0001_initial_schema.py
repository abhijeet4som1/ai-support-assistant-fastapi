"""Initial schema: pgvector extension, tables, enums, HNSW and GIN indexes, generated tsvector,
thinking/total token columns. Replays the original Drizzle SQL files verbatim (alembic/sql/).

Revision ID: 0001
Revises:
Create Date: 2026-10-10
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"
FILES = ["0000_enable_pgvector.sql", "0001_initial_schema.sql", "0002_flawless_mach_iv.sql"]


def upgrade() -> None:
    for name in FILES:
        for statement in (SQL_DIR / name).read_text().split("--> statement-breakpoint"):
            if statement.strip():
                op.execute(statement)


def downgrade() -> None:
    for table in (
        "feedback",
        "messages",
        "conversations",
        "guideline_chunks",
        "refresh_tokens",
    ):
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
    op.execute(
        'ALTER TABLE "companies" DROP CONSTRAINT IF EXISTS '
        '"companies_active_guideline_version_id_guideline_versions_id_fk"'
    )
    op.execute('DROP TABLE IF EXISTS "guideline_versions" CASCADE')
    op.execute('DROP TABLE IF EXISTS "companies" CASCADE')
    op.execute('DROP TABLE IF EXISTS "users" CASCADE')
    for enum in (
        "coverage",
        "feedback_rating",
        "guideline_status",
        "message_role",
        "message_status",
    ):
        op.execute(f'DROP TYPE IF EXISTS "{enum}"')
