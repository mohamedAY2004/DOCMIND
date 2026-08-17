"""Persist structured citations and generation state on messages.

Revision ID: 0006_grounded_messages
Revises: 0005_semester_dates
Create Date: 2026-08-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0006_grounded_messages"
down_revision = "0005_semester_dates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    generation_status = postgresql.ENUM(
        "generating", "complete", "cancelled", "failed", name="generation_status"
    )
    grounding_status = postgresql.ENUM(
        "grounded",
        "partially_grounded",
        "ungrounded",
        "no_context",
        name="grounding_status",
    )
    generation_status.create(op.get_bind(), checkfirst=True)
    grounding_status.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "messages",
        sa.Column(
            "citations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "messages",
        sa.Column(
            "generation_status",
            generation_status,
            nullable=False,
            server_default="complete",
        ),
    )
    op.add_column(
        "messages",
        sa.Column("grounding_status", grounding_status, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("messages", "grounding_status")
    op.drop_column("messages", "generation_status")
    op.drop_column("messages", "citations")
    postgresql.ENUM(name="grounding_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="generation_status").drop(op.get_bind(), checkfirst=True)
