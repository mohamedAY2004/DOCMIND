"""Add instructor_subject_role to subject_instructors.

Each subject now has exactly one "super" instructor who may upload/delete
materials; all others are "viewer" instructors (read-only + test-bot access).

Revision ID: 0002_instructor_subject_role
Revises: 0001_initial
Create Date: 2026-06-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0002_instructor_subject_role"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the new enum type idempotently.
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE instructor_subject_role AS ENUM ('super', 'viewer');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END
        $$;
        """
    )

    # Add the column with a server-side default so existing rows get 'viewer'.
    op.add_column(
        "subject_instructors",
        sa.Column(
            "instructor_role",
            postgresql.ENUM(
                "super",
                "viewer",
                name="instructor_subject_role",
                create_type=False,
            ),
            nullable=False,
            server_default="viewer",
        ),
    )

    # Backfill: for each subject promote the instructor with the most uploads
    # to 'super'. Falls back to the first user_id alphabetically when no
    # uploads exist for that subject.
    op.execute(
        """
        WITH ranked AS (
            SELECT
                si.subject_id,
                si.user_id,
                ROW_NUMBER() OVER (
                    PARTITION BY si.subject_id
                    ORDER BY COALESCE(upl.upload_count, 0) DESC, si.user_id ASC
                ) AS rn
            FROM subject_instructors si
            LEFT JOIN (
                SELECT subject_id, uploaded_by_id, COUNT(*) AS upload_count
                FROM materials
                WHERE uploaded_by_id IS NOT NULL
                GROUP BY subject_id, uploaded_by_id
            ) upl
            ON upl.subject_id = si.subject_id
            AND upl.uploaded_by_id = si.user_id
        )
        UPDATE subject_instructors si
        SET instructor_role = 'super'
        FROM ranked
        WHERE si.subject_id = ranked.subject_id
          AND si.user_id = ranked.user_id
          AND ranked.rn = 1
        """
    )


def downgrade() -> None:
    op.drop_column("subject_instructors", "instructor_role")
    op.execute("DROP TYPE IF EXISTS instructor_subject_role")
