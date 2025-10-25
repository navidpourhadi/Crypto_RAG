from datetime import datetime
from typing import Any, Dict
from uuid import UUID, uuid4

from beanie import Document
from pydantic import Field


class Chat(Document):
    """
    Chat model representing a chat in the system.
    """

    id: UUID = Field(default_factory=uuid4, alias="_id")
    title: str = Field(default="", description="Title of the chat")
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the chat was created",
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the chat was last modified",
    )
    is_active: bool = Field(default=True, description="Is the chat active")

    class Settings:
        name = "chats"
