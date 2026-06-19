"""Add a 'failed' value to the material/document-file status enums.

Background indexing can throw; without a terminal failure state the row stays
stuck in 'indexing'/'processing' forever. This adds 'failed' to both Postgres
enum types so the services can surface the error.

Revision ID: 0003_failed_index_status
Revises: 0002_instructor_subject_role
Create Date: 2026-06-19
"""
from alembic import op


revision = "0003_failed_index_status"
down_revision = "0002_instructor_subject_role"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ADD VALUE is safe inside the migration transaction on PG12+ because the new
    # value is not *used* in this same transaction. IF NOT EXISTS keeps it
    # idempotent across re-runs.
    op.execute("ALTER TYPE material_status ADD VALUE IF NOT EXISTS 'failed'")
    op.execute("ALTER TYPE document_file_status ADD VALUE IF NOT EXISTS 'failed'")


def downgrade() -> None:
    # Postgres cannot drop a value from an enum type, so this is a no-op.
    # (Removing it safely would require recreating the type and rewriting every
    # dependent column — out of scope for a downgrade.)
    pass
