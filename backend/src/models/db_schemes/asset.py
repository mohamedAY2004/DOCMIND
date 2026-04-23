from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Asset(BaseModel):
    id: Optional[int] = Field(None)
    asset_project_id: int
    asset_type: str = Field(..., min_length=1)
    asset_name: str = Field(..., min_length=1)
    asset_size: int = Field(gt=0, default=None)
    asset_config: dict = Field(default=None)
    asset_pushed_at: datetime = Field(default_factory=datetime.utcnow)
