from pydantic import BaseModel, Field, validator
from typing import Optional

class Project(BaseModel):
    id: Optional[int] = Field(None)
    project_id: str = Field(..., min_length=1)

    @validator('project_id')
    def validate_project_id(cls, value):
        if not value.isalnum():
            raise ValueError('project_id must be alphanumeric')
        return value
