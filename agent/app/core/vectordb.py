"""
Qdrant vector database client configuration.
Supports both local and cloud deployments.
"""

import asyncio
from typing import Dict

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class VectorDatabase:
    """Async-safe manager for Qdrant vector database connections."""

    _clients: Dict[str, AsyncQdrantClient] = {}
    _locks: Dict[str, asyncio.Lock] = {}
    _initialized: Dict[str, bool] = {}
    _global_lock = asyncio.Lock()

    @classmethod
    async def get_client(cls, kind: str = "default") -> AsyncQdrantClient:
        """
        Async-safe accessor for named Qdrant clients.
        Initializes client if it doesn't exist.

        Args:
            kind: Client type identifier (default, analytics, etc.)

        Returns:
            QdrantClient: Configured Qdrant client

        Raises:
            ConnectionError: If client initialization fails
        """
        if not settings.QDRANT_URL:
            raise RuntimeError("Qdrant URL is not configured in settings")

        if kind not in cls._clients or not cls._initialized.get(kind, False):
            lock = await cls._get_lock(kind)
            async with lock:
                if kind not in cls._clients or not cls._initialized.get(kind, False):
                    try:
                        if settings.QDRANT_API_KEY:
                            client = AsyncQdrantClient(
                                url=settings.QDRANT_URL,
                                api_key=settings.QDRANT_API_KEY,
                            )  # noqa

                        else:  # No API key, use basic connection
                            client = AsyncQdrantClient(
                                url=settings.QDRANT_URL,
                            )

                        await cls._ensure_collection_exists(
                            client=client,
                            collection_name=settings.QDRANT_COLLECTION_NAME,
                            vector_size=settings.EMBEDDING_DIMENSION,
                        )
                        cls._clients[kind] = client
                        cls._initialized[kind] = True

                        logger.info(f"Qdrant ({kind}) client initialized successfully.")

                    except Exception as e:
                        logger.error(f"Qdrant ({kind}) connection failed: {e}")
                        if kind in cls._clients:
                            del cls._clients[kind]
                        cls._initialized[kind] = False
                        raise RuntimeError(f"Vector DB init error: {e}")

        return cls._clients[kind]

    @staticmethod
    async def collection_exists(client: AsyncQdrantClient) -> bool:
        # check if the Vector db contains any collections
        collections = await client.list_collections()
        return len(collections) > 0
    

    

    
    @staticmethod
    async def _ensure_collection_exists(
        client: AsyncQdrantClient,
        collection_name: str,
        vector_size: int,
    ) -> None:
        """
        Ensure the specified collection exists, creating it if necessary.

        Args:
            client: Qdrant client instance
            collection_name: Name of the collection to check/create
        """
        exists = await client.collection_exists(collection_name)
        if not exists:
            await client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )
        else:
            # get collection info size
            collection_info = await client.get_collection(collection_name)
            collection_vector_size = collection_info.config.params.vectors.size
            if collection_vector_size != vector_size:
                logger.error(
                    f"Collection '{collection_name}' exists with size: "
                    f"{collection_vector_size}, but expected size: {vector_size}."
                )

    @classmethod
    async def _get_lock(cls, kind: str) -> asyncio.Lock:
        """Get or create an async lock for the specified client type."""
        if kind not in cls._locks:
            async with cls._global_lock:
                if kind not in cls._locks:
                    cls._locks[kind] = asyncio.Lock()
        return cls._locks[kind]

    @classmethod
    async def close(cls, kind: str = None) -> None:
        """
        Close Qdrant connection(s).

        Args:
            kind: Optional client type to close. If None, closes all connections.
        """
        if kind is not None:
            # Close specific client
            await cls._close_client(kind)
        else:
            # Close all clients
            for client_kind in list(cls._clients.keys()):
                await cls._close_client(client_kind)

    @classmethod
    async def _close_client(cls, kind: str) -> None:
        """Close a specific kind of Qdrant client connection."""
        lock = await cls._get_lock(kind)
        async with lock:
            if kind in cls._clients:
                try:
                    await cls._clients[kind].close()
                    logger.info(f"Qdrant ({kind}) connection closed.")
                except Exception as e:
                    logger.warning(f"Error during close of Qdrant ({kind}): {e}")
                finally:
                    if kind in cls._clients:
                        del cls._clients[kind]
                    cls._initialized[kind] = False

    @staticmethod
    def run_in_threadpool(func):
        """
        Decorator to run a synchronous client method in a thread pool.
        Useful for wrapping blocking Qdrant client calls.

        Args:
            func: The synchronous function to run in a thread pool

        Returns:
            Async wrapper function
        """
        from functools import wraps

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await asyncio.to_thread(func, *args, **kwargs)

        return wrapper
