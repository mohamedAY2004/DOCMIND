"""Add evaluation, feedback review, telemetry, storage, and retention fields.

Revision ID: 0008_pilot_quality
Revises: 0007_refresh_sessions
Create Date: 2026-08-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0008_pilot_quality"
down_revision = "0007_refresh_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_status_values = ("queued", "running", "completed", "failed")
    feedback_reason_values = ("incorrect", "unsupported", "outdated", "unclear", "incomplete", "other")
    postgresql.ENUM(*run_status_values, name="evaluation_run_status").create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(*feedback_reason_values, name="feedback_reason").create(op.get_bind(), checkfirst=True)
    run_status = postgresql.ENUM(*run_status_values, name="evaluation_run_status", create_type=False)
    feedback_reason = postgresql.ENUM(*feedback_reason_values, name="feedback_reason", create_type=False)
    op.create_table(
        "evaluation_cases",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("subject_id", sa.String(), sa.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("reference_answer", sa.Text(), nullable=False),
        sa.Column("expected_material_ids", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("tags", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by_id", sa.String(32), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_evaluation_cases_subject_id", "evaluation_cases", ["subject_id"])
    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("subject_id", sa.String(), sa.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", run_status, nullable=False, server_default="queued"),
        sa.Column("corpus_version", sa.String(128), nullable=False),
        sa.Column("pipeline_snapshot", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("summary_metrics", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("failure", sa.Text()),
        sa.Column("created_by_id", sa.String(32), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_evaluation_runs_subject_id", "evaluation_runs", ["subject_id"])
    op.create_table(
        "evaluation_results",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("run_id", sa.String(40), sa.ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("case_id", sa.String(40), sa.ForeignKey("evaluation_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("generated_answer", sa.Text(), nullable=False, server_default=""),
        sa.Column("citations", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("metrics", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("failure_info", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_evaluation_results_run_id", "evaluation_results", ["run_id"])
    op.create_table(
        "generation_telemetry",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("message_id", sa.String(40), sa.ForeignKey("messages.id", ondelete="SET NULL")),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("subject_id", sa.String(), sa.ForeignKey("subjects.id", ondelete="SET NULL")),
        sa.Column("pipeline_flags", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("retrieval_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("top_score", sa.Float()),
        sa.Column("time_to_first_token_ms", sa.Integer()),
        sa.Column("total_latency_ms", sa.Integer()),
        sa.Column("completion_state", sa.String(32), nullable=False),
        sa.Column("error_code", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_generation_telemetry_message_id", "generation_telemetry", ["message_id"])
    op.add_column("feedbacks", sa.Column("reason", feedback_reason, nullable=True))
    op.add_column("feedbacks", sa.Column("comment", sa.String(500), nullable=True))
    op.add_column("feedbacks", sa.Column("evaluation_case_id", sa.String(40), sa.ForeignKey("evaluation_cases.id", ondelete="SET NULL"), nullable=True))
    op.add_column("conversations", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_conversations_expires_at", "conversations", ["expires_at"])
    op.execute(
        """
        UPDATE conversations c SET expires_at = CASE
          WHEN c.kind = 'tutor' THEN COALESCE(
            (SELECT (s.end_date::timestamp AT TIME ZONE 'UTC') + interval '30 days'
             FROM subjects sub JOIN semesters s ON s.id = sub.semester_id
             WHERE sub.id = c.subject_id),
            c.created_at + interval '180 days'
          )
          ELSE COALESCE(
            (SELECT (max(s.end_date)::timestamp AT TIME ZONE 'UTC') + interval '30 days'
             FROM semesters s
             WHERE (s.start_date IS NULL OR s.start_date <= CURRENT_DATE)
               AND (s.end_date IS NULL OR s.end_date >= CURRENT_DATE)),
            c.created_at + interval '180 days'
          )
        END
        """
    )
    for table in ("materials", "document_files"):
        op.add_column(table, sa.Column("storage_key", sa.String(1024), nullable=True))
        op.add_column(table, sa.Column("storage_backend", sa.String(20), nullable=False, server_default="local"))


def downgrade() -> None:
    for table in ("document_files", "materials"):
        op.drop_column(table, "storage_backend")
        op.drop_column(table, "storage_key")
    op.drop_index("ix_conversations_expires_at", table_name="conversations")
    op.drop_column("conversations", "expires_at")
    op.drop_column("feedbacks", "evaluation_case_id")
    op.drop_column("feedbacks", "comment")
    op.drop_column("feedbacks", "reason")
    op.drop_index("ix_generation_telemetry_message_id", table_name="generation_telemetry")
    op.drop_table("generation_telemetry")
    op.drop_index("ix_evaluation_results_run_id", table_name="evaluation_results")
    op.drop_table("evaluation_results")
    op.drop_index("ix_evaluation_runs_subject_id", table_name="evaluation_runs")
    op.drop_table("evaluation_runs")
    op.drop_index("ix_evaluation_cases_subject_id", table_name="evaluation_cases")
    op.drop_table("evaluation_cases")
    postgresql.ENUM(name="feedback_reason").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="evaluation_run_status").drop(op.get_bind(), checkfirst=True)
