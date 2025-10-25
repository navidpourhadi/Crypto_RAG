import asyncio
from typing import List

import aiohttp

from app.core.config import settings
from app.utils.logger import get_logger

from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = get_logger(__name__)


class ChunkService:
    """
    Service class for Chunking text and PDF files.
    """

    @staticmethod
    async def chunk_text(
        text: str,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP,
    ) -> List[str]:
        """
        Chunk text into smaller chunks.

        Args:
            text: Text to chunk
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks

        Returns:
            List of chunks
        """
        # Run CPU-intensive text splitting in a thread pool
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

        # Use asyncio.to_thread to run CPU-intensive operations without blocking
        chunks = await asyncio.to_thread(text_splitter.split_text, text)
        return chunks
