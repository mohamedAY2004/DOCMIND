"""Drop empty retired tables after the explicit legacy-data cleanup."""
from alembic import op
from sqlalchemy import inspect, text

revision = "0012_retire_debug_schema"
down_revision = "0011_vector_schema"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())
    legacy = [name for name in ("data_chunks", "assets", "projects") if name in tables]
    for name in legacy:
        if bind.execute(text(f'SELECT EXISTS (SELECT 1 FROM "{name}")')).scalar():
            raise RuntimeError("Legacy data remains. Run python -m scripts.cleanup_legacy --apply before upgrading.")
    for name in legacy:
        op.drop_table(name)


def downgrade():
    raise RuntimeError("Legacy deletion is irreversible; restore a pre-cleanup backup to run the retired API.")
