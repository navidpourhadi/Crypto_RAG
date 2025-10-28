from typing import Any, Dict, List
from pydantic import BaseModel, Field

from datetime import datetime


class CreateNews(BaseModel):
    id: str = Field(..., description="Unique identifier")
    title: str = Field(..., description="Title of the news")
    time: datetime = Field(..., description="Time of publication")
    source: str = Field(..., description="Source of the news")
    description: str = Field(..., description="Description of the news")
    VDB_added_at: datetime | None = Field(
        None, description="Timestamp of adding to the vector db"
    )


class UpdateNews(BaseModel):
    id: str | None = Field(..., description="Unique identifier")
    title: str | None = Field(..., description="Title of the news")
    time: datetime | None = Field(..., description="Time of publication")
    source: str | None = Field(..., description="Source of the news")
    description: str | None = Field(..., description="Description of the news")
    VDB_added_at: datetime | None = Field(
        ..., description="Timestamp of adding to the vector db"
    )


class NewsResponse(BaseModel):
    """
    Schema for the response of a News.
    """

    id: str = Field(..., description="Unique identifier")
    title: str = Field(..., description="Title of the news")
    time: datetime = Field(..., description="Time of publication")
    source: str = Field(..., description="Source of the news")
    description: str = Field(..., description="Description of the news")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    VDB_added_at: datetime | None = Field(
        ..., description="Timestamp of adding to the vector db"
    )