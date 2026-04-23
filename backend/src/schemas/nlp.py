from pydantic import BaseModel
from typing import Optional
class PushRequest(BaseModel):
    do_reset: Optional[int] = 1

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5
    threshold: Optional[float] =0.5

class AnswerRequest(BaseModel):
    query: str
    limit: Optional[int] = 3
    threshold: Optional[float] =0.5