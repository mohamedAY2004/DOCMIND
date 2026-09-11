"""Failures in the persistence contract shared by vector adapters."""
from contextlib import contextmanager


class VectorStoreError(RuntimeError):
    """A requested vector operation did not complete successfully."""


@contextmanager
def vector_write():
    """Translate validation, conversion and provider failures at the write boundary."""
    try:
        yield
    except VectorStoreError:
        raise
    except Exception as exc:
        raise VectorStoreError("Vector write did not complete") from exc


def validate_batch(texts, vectors, metadata, record_ids, batch_size):
    if batch_size < 1:
        raise VectorStoreError("Vector batch size must be positive")
    if record_ids is None or any(not isinstance(value, str) or not value for value in record_ids):
        raise VectorStoreError("Every vector needs a stable nonempty string ID")
    if len(set(record_ids)) != len(record_ids):
        raise VectorStoreError("Vector IDs must be unique within a write")
    if not len(texts) == len(vectors) == len(metadata) == len(record_ids):
        raise VectorStoreError("Vector batch lengths must match")
