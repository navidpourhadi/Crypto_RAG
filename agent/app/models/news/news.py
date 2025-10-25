from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field


class News(Document):
    """
    Model representing a news from the newsletter.
    """

    id: str = Field(..., description="Unique identifier")
    title: str = Field(..., description="Title of the news")
    time: datetime = Field(..., description="Time of publication")
    source: str = Field(..., description="Source of the news")
    description: str = Field(..., description="Description of the news")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    VDB_added_at: datetime = Field(
        ..., description="Timestamp of adding to the vector db"
    )

    class Settings:
        name = "news"
