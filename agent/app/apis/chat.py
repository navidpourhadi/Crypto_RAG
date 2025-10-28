from typing import List
from uuid import UUID

from fastapi.routing import APIRouter

from app.models.chats.chat_schema import ChatResponse, ChatUpdate
from app.services.chat import ChatService

router = APIRouter(prefix="/chat")


@router.get("/", response_model=List[ChatResponse])
async def get_all_chats():
    """
    Get all chats.
    """

    return await ChatService.get_all_chats()


@router.post("/")
async def start_chat(
    user_message: str,
):
    """
    Start a new chat.
    """

    return await ChatService.chat_with_agent(user_message=user_message)


@router.post("/{chat_id}")
async def chat(
    chat_id: UUID,
    user_message: str,
):
    """
    Get a chat by ID for the current user via cookie.
    """
    return await ChatService.chat_with_agent(
        user_message=user_message,
        chat_id=chat_id,
    )


@router.get("/{chat_id}")
async def get_chat_history(
    chat_id: UUID,
):
    """
    Get a chat history by chat ID.
    """
    return await ChatService.get_chat_history(chat_id=chat_id)


@router.put("/{chat_id}")
async def update_chat(
    chat_id: UUID,
    chat_data: ChatUpdate,
):
    """
    Update a chat by ID for the current user via cookie.
    """
    return await ChatService.update_chat(
        chat_id=chat_id,
        new_data=chat_data,
    )


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: UUID,
):
    """
    Delete a chat by ID for the current user via cookie.
    """
    return await ChatService.delete_chat(chat_id=chat_id)
