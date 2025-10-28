from datetime import datetime
from typing import Dict, List
from uuid import UUID

from beanie.operators import In, Set
from langchain_core.messages import AIMessage, HumanMessage

from app.agent.agent import get_agent
from app.models.chats.chat import Chat
from app.models.chats.chat_schema import ChatCreate, ChatResponse, ChatUpdate
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ChatService:
    """
    Service class for handling chat-related operations.
    """

    @staticmethod
    async def create_chat(title: str = None) -> Chat:
        if title:
            chat = Chat(title=title)
        else:
            chat = Chat()
        await chat.insert()
        return chat

    @staticmethod
    async def update_chat(chat_id: UUID, new_data: ChatUpdate) -> Chat | None:
        chat = await Chat.get(chat_id)
        if not chat:
            logger.error(f"Chat with ID {chat_id} not found.")
        update_data = {k: v for k, v in new_data.model_dump().items() if v is not None}
        if update_data:
            await chat.update(Set(update_data))
        chat.updated_at = datetime.now()
        await chat.save()
        return chat

    @staticmethod
    async def delete_chat(chat_id: UUID) -> Chat | None:
        chat = await Chat.get(chat_id)
        if not chat:
            logger.error(f"Chat with ID {chat_id} not found.")
        await chat.delete()
        return chat

    @staticmethod
    async def get_chat(chat_id: UUID) -> Chat | None:
        return await Chat.get(chat_id)

    @staticmethod
    async def get_all_chats() -> List[Chat]:
        return await Chat.find().to_list()

    @staticmethod
    async def chat_with_agent(
        user_message: str,
        chat_id: UUID | None = None,
    ) -> Dict:
        """
        Send a message to the agent and get a response.
        """
        new_chat = False
        agent = await get_agent()
        if not chat_id:
            new_chat = True
            chat = await ChatService.create_chat(
                title=user_message[:25],
            )
            chat_id = chat.id

        user_message = HumanMessage(
            content=user_message,
            additional_kwargs={
                "timestamp": datetime.now().isoformat(),
            },
        )
        agent_response = await agent.generate_response(
            user_input=user_message,
            thread_id=chat_id,
        )
        if not new_chat:
            await ChatService.update_chat(
                chat_id=chat_id,
                new_data=ChatUpdate(updated_at=datetime.now()),
            )
        return {
            "chat_id": chat_id,
            "user_message": user_message.content,
            "agent_response": agent_response,
        }

    @staticmethod
    async def get_chat_history(chat_id: str) -> List[Dict] | None:
        """
        Retrieve the conversation history for a specific chat ID.
        """
        agent = await get_agent()

        thread_config = {"configurable": {"thread_id": chat_id}}

        state = await agent.graph.aget_state(thread_config)

        if state and hasattr(state, "values") and "messages" in state.values:
            # Filter out tool messages and system messages, only keep user and assistant
            filtered_messages = []
            for msg in state.values["messages"]:
                if isinstance(msg, HumanMessage):
                    filtered_messages.append(
                        {
                            "content": msg.content,
                            "role": "user",
                            "timestamp": msg.additional_kwargs.get("timestamp", None)
                            if hasattr(msg, "additional_kwargs")
                            else None,
                        }
                    )
                elif isinstance(msg, AIMessage) and (
                    not hasattr(msg, "tool_calls") or not msg.tool_calls
                ):
                    # Only include AI messages that are not tool calls
                    filtered_messages.append(
                        {
                            "content": msg.content,
                            "role": "assistant",
                            "timestamp": msg.additional_kwargs.get("timestamp", None)
                            if hasattr(msg, "additional_kwargs")
                            else None,
                        }
                    )

            return filtered_messages

        return None
