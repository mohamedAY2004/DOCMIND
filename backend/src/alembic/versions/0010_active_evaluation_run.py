"""Prevent concurrent active evaluation runs for one subject.

Revision ID: 0010_active_evaluation_run
Revises: 0009_message_order
Create Date: 2026-08-17
"""
from alembic import op

revision = "0010_active_evaluation_run"
down_revision = "0009_message_order"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "WITH ranked AS ("
        " SELECT id, row_number() OVER (PARTITION BY subject_id ORDER BY created_at) AS rn"
        " FROM evaluation_runs WHERE status IN ('queued', 'running')"
        ") UPDATE evaluation_runs SET status = 'failed',"
        " failure = 'Superseded while enforcing one active run per subject'"
        " WHERE id IN (SELECT id FROM ranked WHERE rn > 1)"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_evaluation_runs_active_subject "
        "ON evaluation_runs (subject_id) "
        "WHERE status IN ('queued', 'running')"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_evaluation_runs_active_subject")
