"""Fixed vector-store schema; provisioning is owned by Alembic."""
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from db.base import Base


class VectorCollection(Base):
    __tablename__ = "vector_collections"
    collection_name: Mapped[str] = mapped_column(String, primary_key=True)
    embedding_size: Mapped[int] = mapped_column(Integer)
    distance_method: Mapped[str] = mapped_column(String, server_default="cosine")


class VectorEmbedding(Base):
    __tablename__ = "vector_embeddings"
    __table_args__ = (Index("idx_embeddings_collection", "collection_name"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    collection_name: Mapped[str] = mapped_column(ForeignKey("vector_collections.collection_name", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    embedding: Mapped[list | None] = mapped_column(Vector(), nullable=True)
