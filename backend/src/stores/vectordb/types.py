"""Provider-independent retrieval values."""
from pydantic import BaseModel
from typing import List, Optional

class RetrievedChunk(BaseModel):
    chunk_text: str
    score: float
    chunk_metadata: dict
    # Populated only when search is called with ``with_vectors=True`` (the MMR
    # path); None everywhere else so existing payloads stay unchanged.
    embedding: Optional[List[float]] = None
