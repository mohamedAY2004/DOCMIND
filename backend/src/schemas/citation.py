from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CitationViewResponse(BaseModel):
    url: str
    expiresAt: datetime
    sourceName: str
    locationType: str
    locationNumber: int
    section: Optional[str] = None
    excerpt: str
