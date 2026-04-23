"""Initial DocMind schema.

Creates every table the new backend owns. The vectordb provider
(``PgVectorProvider``) still owns its own ``vector_collections`` /
``vector_embeddings`` tables which it creates at application startup.

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    # The legacy tables (projects/assets/data_chunks) may already exist from
    # the pre-Alembic startup path. Skip re-creating them in that case so the
    # initial migration stays idempotent against older dev databases.
    return inspect(op.get_bind()).has_table(name)


def upgrade() -> None:
    # pgvector extension (spec §7.4 — required for semantic search).
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ------------------------------------------------------------------
    # Legacy tables (kept so /api/v1/data/* and /api/v1/nlp/* debug routes
    # continue to work. They are not part of the DocMind spec.)
    # ------------------------------------------------------------------
    if not _has_table("projects"):
        op.create_table(
            "projects",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("project_id", sa.String, nullable=False, unique=True),
        )
    if not _has_table("assets"):
        op.create_table(
            "assets",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column(
                "asset_project_id",
                sa.Integer,
                sa.ForeignKey("projects.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("asset_type", sa.String, nullable=False),
            sa.Column("asset_name", sa.String, nullable=False),
            sa.Column("asset_size", sa.Integer),
            sa.Column("asset_config", postgresql.JSONB),
            sa.Column(
                "asset_pushed_at",
                sa.DateTime(timezone=False),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.UniqueConstraint("asset_name", "asset_project_id", name="uq_assets_name_project"),
        )
        op.create_index("idx_assets_project_id", "assets", ["asset_project_id"])

    if not _has_table("data_chunks"):
        op.create_table(
            "data_chunks",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("chunk_text", sa.Text, nullable=False),
            sa.Column("chunk_metadata", postgresql.JSONB, nullable=False),
            sa.Column("chunk_order", sa.Integer, nullable=False),
            sa.Column(
                "chunk_project_id",
                sa.Integer,
                sa.ForeignKey("projects.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "chunk_asset_id",
                sa.Integer,
                sa.ForeignKey("assets.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.CheckConstraint("chunk_order > 0", name="ck_chunks_order_positive"),
        )
        op.create_index("idx_chunks_project_id", "data_chunks", ["chunk_project_id"])

    # ------------------------------------------------------------------
    # DocMind domain
    # ------------------------------------------------------------------
    # Enum types are created idempotently via DO blocks so the migration is
    # safe against databases where a previous half-applied run left the types
    # behind. Subsequent table definitions reference them with
    # ``postgresql.ENUM(..., create_type=False)`` so SQLAlchemy never re-emits
    # ``CREATE TYPE`` during ``op.create_table(...)``.
    _ENUMS = {
        "user_role": ("student", "instructor", "admin"),
        "user_status": ("active", "disabled"),
        "material_status": ("indexing", "processed"),
        "conversation_kind": ("doc", "tutor"),
        "document_file_status": ("processing", "ready"),
        "message_role": ("user", "assistant", "doc"),
        "feedback_value": ("up", "down"),
    }
    for _name, _values in _ENUMS.items():
        _literals = ", ".join(f"'{v}'" for v in _values)
        op.execute(
            f"""
            DO $$
            BEGIN
                CREATE TYPE {_name} AS ENUM ({_literals});
            EXCEPTION
                WHEN duplicate_object THEN null;
            END
            $$;
            """
        )

    op.create_table(
        "users",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column(
            "role",
            postgresql.ENUM("student", "instructor", "admin", name="user_role", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM("active", "disabled", name="user_status", create_type=False),
            nullable=False,
            server_default="active",
        ),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_active", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "semesters",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
    )

    op.create_table(
        "subjects",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("course_code", sa.String(80), nullable=False),
        sa.Column(
            "semester_id",
            sa.String(64),
            sa.ForeignKey("semesters.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "subject_instructors",
        sa.Column(
            "subject_id",
            sa.String(64),
            sa.ForeignKey("subjects.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            sa.String(32),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "subject_students",
        sa.Column(
            "subject_id",
            sa.String(64),
            sa.ForeignKey("subjects.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            sa.String(32),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "materials",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "subject_id",
            sa.String(64),
            sa.ForeignKey("subjects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=False),
        sa.Column("mime", sa.String(120), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "indexing", "processed", name="material_status", create_type=False
            ),
            nullable=False,
            server_default="indexing",
        ),
        sa.Column(
            "uploaded_by_id",
            sa.String(32),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "conversations",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column(
            "owner_id",
            sa.String(32),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "kind",
            postgresql.ENUM("doc", "tutor", name="conversation_kind", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "subject_id",
            sa.String(64),
            sa.ForeignKey("subjects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(120), nullable=False, server_default="New Chat"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "document_files",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.String(40),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=False),
        sa.Column("mime", sa.String(120), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "processing", "ready", name="document_file_status", create_type=False
            ),
            nullable=False,
            server_default="processing",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.String(40),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "role",
            postgresql.ENUM("user", "assistant", "doc", name="message_role", create_type=False),
            nullable=False,
        ),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "feedbacks",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column(
            "message_id",
            sa.String(40),
            sa.ForeignKey("messages.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "user_id",
            sa.String(32),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "feedback",
            postgresql.ENUM("up", "down", name="feedback_value", create_type=False),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "activities",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("action", sa.String(160), nullable=False),
        sa.Column(
            "actor_user_id",
            sa.String(32),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("subject_label", sa.String(200), nullable=True),
        sa.Column("meta", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "student_access_flag",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("message", sa.String(500), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "token_blocklist",
        sa.Column("jti", sa.String(64), primary_key=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("token_blocklist")
    op.drop_table("student_access_flag")
    op.drop_table("activities")
    op.drop_table("feedbacks")
    op.drop_table("messages")
    op.drop_table("document_files")
    op.drop_table("conversations")
    op.drop_table("materials")
    op.drop_table("subject_students")
    op.drop_table("subject_instructors")
    op.drop_table("subjects")
    op.drop_table("semesters")
    op.drop_table("users")

    for enum_name in [
        "feedback_value",
        "message_role",
        "document_file_status",
        "conversation_kind",
        "material_status",
        "user_status",
        "user_role",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")

    op.drop_index("idx_chunks_project_id", table_name="data_chunks")
    op.drop_table("data_chunks")
    op.drop_index("idx_assets_project_id", table_name="assets")
    op.drop_table("assets")
    op.drop_table("projects")
