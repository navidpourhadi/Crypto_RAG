import asyncio
import threading
from functools import wraps
from typing import Callable, Dict

from google import genai
from google.genai import types

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GenAIClientManager:
    _clients: Dict[str, genai.Client] = {}
    _locks: Dict[str, asyncio.Lock] = {}
    _global_lock = asyncio.Lock()

    @classmethod
    async def get_client(cls, kind: str = "default") -> genai.Client:
        if kind not in cls._clients:
            lock = await cls._get_lock(kind)
            async with lock:
                if kind not in cls._clients:
                    try:
                        # Note: If genai.Client initialization is blocking,
                        # consider using run_in_executor
                        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
                        cls._clients[kind] = client
                        logger.info(
                            f"Google GenAI client '{kind}' initialized successfully."
                        )  # noqa: E501
                    except Exception as e:
                        logger.error(
                            f"Failed to initialize Google GenAI client '{kind}': {e}"
                        )  # noqa: E501
                        raise RuntimeError(
                            f"Failed to initialize Google GenAI client '{kind}': {e}"
                        )

        return cls._clients[kind]

    @classmethod
    async def _get_lock(cls, kind: str) -> asyncio.Lock:
        if kind not in cls._locks:
            async with cls._global_lock:
                if kind not in cls._locks:
                    cls._locks[kind] = asyncio.Lock()
        return cls._locks[kind]

    @staticmethod
    def run_in_threadpool(func: Callable) -> Callable:
        """
        Decorator to run a synchronous client method in a thread pool.
        Useful for wrapping blocking GenAI client calls.

        Args:
            func: The synchronous function to run in a thread pool

        Returns:
            Async wrapper function
        """

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await asyncio.to_thread(func, *args, **kwargs)

        return wrapper
