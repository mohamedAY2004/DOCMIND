from pydantic import BaseModel, Field
from typing import Optional

class DataChunk(BaseModel):
    id: Optional[int] = Field(None)
    chunk_text: str = Field(..., min_length=1)
    chunk_metadata: dict
    chunk_order: int = Field(..., gt=0)
    chunk_project_id: int
    chunk_asset_id: int

class RetrievedChunk(BaseModel):
    chunk_text: str
    score: float
    chunk_metadata: dict
