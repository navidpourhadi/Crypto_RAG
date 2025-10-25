import asyncio
from typing import List, Type

from beanie import Document, init_beanie
from pymongo import AsyncMongoClient

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MongoDatabase:
    client: AsyncMongoClient | None = None
    _instance = None
    _initialized = False
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    async def initialize(cls, document_models: List[Type[Document]]):
        """Initialize database connection and Beanie ODM."""
        async with cls._lock:
            if cls._initialized:
                return

            # Create Motor client
            cls.client = AsyncMongoClient(settings.MONGO_URI)

            # Initialize Beanie with the document models
            await init_beanie(
                database=cls.client[settings.MONGO_DB_NAME],
                document_models=document_models,
            )

            cls._initialized = True
            logger.info(f"Database initialized with {len(document_models)} models")

    @classmethod
    async def close(cls):
        """Close database connection."""
        if cls.client:
            cls.client.close()
            cls.client = None
            cls._initialized = False
            cls._instance = None
            logger.info("Database connection closed")

    @classmethod
    def get_client(cls) -> AsyncMongoClient:
        """Get the database client."""
        if not cls.client:
            raise ConnectionError("Database not initialized. Call initialize() first.")
        return cls.client

    @classmethod
    def get_db(cls):
        """Get the database instance."""
        if not cls.client:
            raise ConnectionError("Database not initialized. Call initialize() first.")
        return cls.client[settings.MONGO_DB_NAME]
