"""Add start_date / end_date to semesters.

Semesters gain an optional date window. The lifecycle state (upcoming / active /
archived) is *derived* from these dates in application code (see
``db.models.semester.derive_semester_state``) rather than stored, so there is no
enum type to create here — just two nullable date columns plus a backfill.

The backfill mirrors the seed's term convention
(``seeds.seed_initial._semester_start``): ids shaped ``<term>-<year>`` get a
start on the 1st of the term month (fall → September, otherwise February) and an
end ~4 months later. Ids that don't match the pattern stay NULL, which the
derivation treats as "always active".

Revision ID: 0005_semester_dates
Revises: 0004_one_super_per_subject
Create Date: 2026-06-21
"""
from alembic import op
import sqlalchemy as sa


revision = "0005_semester_dates"
down_revision = "0004_one_super_per_subject"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("semesters", sa.Column("start_date", sa.Date(), nullable=True))
    op.add_column("semesters", sa.Column("end_date", sa.Date(), nullable=True))

    # Backfill from the "<term>-<year>" id convention. fall → Sep–Dec,
    # spring/other → Feb–May. Admins can adjust afterwards via PATCH.
    op.execute(
        """
        UPDATE semesters SET
            start_date = make_date(
                split_part(id, '-', 2)::int,
                CASE WHEN split_part(id, '-', 1) = 'fall' THEN 9 ELSE 2 END,
                1
            ),
            end_date = make_date(
                split_part(id, '-', 2)::int,
                CASE WHEN split_part(id, '-', 1) = 'fall' THEN 12 ELSE 6 END,
                1
            )
        WHERE id LIKE '%-%'
          AND split_part(id, '-', 2) ~ '^[0-9]{4}$'
        """
    )


def downgrade() -> None:
    op.drop_column("semesters", "end_date")
    op.drop_column("semesters", "start_date")
