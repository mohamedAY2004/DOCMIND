"""Enforce at most one 'super' instructor per subject.

The instructor logic assumes each subject has exactly one super instructor.
``replace_instructors`` already guarantees this on the write path, but nothing
stopped a stray insert from creating a second super. This adds a partial unique
index so the invariant is enforced by the database.

Revision ID: 0004_one_super_per_subject
Revises: 0003_failed_index_status
Create Date: 2026-06-19
"""
from alembic import op


revision = "0004_one_super_per_subject"
down_revision = "0003_failed_index_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_subject_one_super
        ON subject_instructors (subject_id)
        WHERE instructor_role = 'super'
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_subject_one_super")
