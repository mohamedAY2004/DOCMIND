"""Adopt fixed vector tables while preserving existing embeddings and ANN indexes."""
from alembic import op
from sqlalchemy import inspect, text

revision = "0011_vector_schema"
down_revision = "0010_active_evaluation_run"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    # Frozen copies of the provider's original DDL: do not import live ORM models.
    op.execute("""CREATE TABLE IF NOT EXISTS vector_collections (
        collection_name VARCHAR PRIMARY KEY,
        embedding_size INTEGER NOT NULL,
        distance_method VARCHAR NOT NULL DEFAULT 'cosine')""")
    op.execute("""CREATE TABLE IF NOT EXISTS vector_embeddings (
        id VARCHAR PRIMARY KEY,
        collection_name VARCHAR NOT NULL REFERENCES vector_collections(collection_name) ON DELETE CASCADE,
        text TEXT NOT NULL,
        metadata JSONB,
        embedding vector)""")
    expected = {
        "vector_collections": {"collection_name": "character varying", "embedding_size": "integer", "distance_method": "character varying"},
        "vector_embeddings": {"id": "character varying", "collection_name": "character varying", "text": "text", "metadata": "jsonb", "embedding": "vector"},
    }
    inspector = inspect(bind)
    for table, columns in expected.items():
        types = dict(bind.execute(text("""SELECT attname, format_type(atttypid, atttypmod)
            FROM pg_attribute WHERE attrelid=to_regclass(:table) AND attnum>0 AND NOT attisdropped"""),
            {"table": table}).all())
        if any(types.get(name) != kind for name, kind in columns.items()):
            raise RuntimeError(f"Incompatible existing {table} schema; reconcile types before migration")
        primary_key = "id" if table == "vector_embeddings" else "collection_name"
        if inspector.get_pk_constraint(table)["constrained_columns"] != [primary_key]:
            raise RuntimeError(f"Incompatible primary key on {table}")
        required = set(columns) - {"metadata", "embedding"}
        if any(c["nullable"] for c in inspector.get_columns(table) if c["name"] in required):
            raise RuntimeError(f"Incompatible nullable columns on {table}")
    foreign_keys = inspector.get_foreign_keys("vector_embeddings")
    if not any(fk["constrained_columns"] == ["collection_name"]
               and fk["referred_table"] == "vector_collections"
               and fk["referred_columns"] == ["collection_name"]
               and fk["options"].get("ondelete") == "CASCADE" for fk in foreign_keys):
        raise RuntimeError("Vector embeddings require a cascading collection foreign key")
    # No ANN indexes are removed/rebuilt. Collections without a matching ANN index use exact search.
    op.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_collection ON vector_embeddings(collection_name)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_material ON vector_embeddings(collection_name, (metadata->>'material_id'))")


def downgrade():
    # The previous provider understands these tables. Keep official embeddings and indexes.
    pass
