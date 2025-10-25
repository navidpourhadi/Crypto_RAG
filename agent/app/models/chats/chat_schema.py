from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field


class ChatCreate(BaseModel):
    """
    Schema for creating a new chat.
    """

    title: str | None = Field(
        title="Title of the chat",
        description="The title of the chat.",
    )


class ChatResponse(BaseModel):
    """
    Schema for the response of a chat.
    """

    id: UUID = Field(
        title="Chat ID",
        description="The unique identifier of the chat.",
    )
    title: str | None = Field(
        title="Title of the chat",
        description="The title of the chat.",
    )
    created_at: datetime = Field(
        title="Creation date",
        description="The date when the chat was created.",
    )
    updated_at: datetime = Field(
        title="Last updated date",
        description="The date when the chat was last updated.",
    )
    is_active: bool = Field(
        title="Is active",
        description="Indicates whether the chat is active.",
    )

    class Config:
        from_attributes = True


class ChatUpdate(BaseModel):
    """
    Schema for updating a chat.
    """

    title: str | None = Field(
        default=None,
        title="Title of the chat",
        description="The title of the chat.",
    )
    is_active: bool | None = Field(
        default=None,
        title="Is active",
        description="Indicates whether the chat is active.",
    )
    updated_at: datetime | None = Field(
        default=None,
        title="Last updated date",
        description="The date when the chat was last updated.",
    )

    class Config:
        from_attributes = True
