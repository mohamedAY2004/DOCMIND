"""Add a stable insertion order for conversation messages.

Revision ID: 0009_message_order
Revises: 0008_pilot_quality
Create Date: 2026-08-17
"""
from alembic import op
import sqlalchemy as sa

revision = "0009_message_order"
down_revision = "0008_pilot_quality"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SEQUENCE message_sort_id_seq")
    op.add_column(
        "messages",
        sa.Column(
            "sort_id",
            sa.BigInteger(),
            server_default=sa.text("nextval('message_sort_id_seq')"),
            nullable=True,
        ),
    )
    op.execute(
        "UPDATE messages AS message SET sort_id = ordered.position "
        "FROM (SELECT id, row_number() OVER (ORDER BY created_at, id) AS position "
        "FROM messages) AS ordered WHERE message.id = ordered.id"
    )
    op.execute(
        "SELECT setval('message_sort_id_seq', "
        "GREATEST(COALESCE((SELECT MAX(sort_id) FROM messages), 0) + 1, 1), false)"
    )
    op.alter_column("messages", "sort_id", nullable=False)
    op.execute("ALTER SEQUENCE message_sort_id_seq OWNED BY messages.sort_id")
    op.create_index("ix_messages_sort_id", "messages", ["sort_id"])


def downgrade() -> None:
    op.drop_index("ix_messages_sort_id", table_name="messages")
    op.drop_column("messages", "sort_id")
    op.execute("DROP SEQUENCE IF EXISTS message_sort_id_seq")
