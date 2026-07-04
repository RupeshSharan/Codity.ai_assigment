from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PageParams(BaseModel):
    limit: int = Field(default=25, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class PaginatedResponse(BaseModel):
    items: list
    total: int
    limit: int
    offset: int


class ErrorResponse(BaseModel):
    error: dict[str, str]


class Timestamped(ORMModel):
    created_at: datetime
    updated_at: datetime

