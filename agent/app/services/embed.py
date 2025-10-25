import asyncio
from typing import List

import aiohttp

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EmbedService:
    """
    Service class for embedding text and PDF files using Google Jina AI.
    """

    @staticmethod
    async def embed_text_jina(
        contents: List[str],
        late_chunking: bool = False,
        truncate: bool = False,
    ) -> List[List[float]]:
        """
        Embed text using Jina AI embedding API.

        Args:
            contents: List of text strings to embed
            task_type: Type of embedding task (text-matching, retrieval-query,
                retrieval-passage, separation, classification, text-embedding)

        Returns:
            List of ContentEmbedding objects
        """

        return await EmbedService._jina_embed_request(
            contents=contents,
            late_chunking=late_chunking,
            truncate=truncate,
        )

    @staticmethod
    async def embed_query_jina(
        contents: List[str],
    ) -> List[List[float]]:
        """
        Embed query text using Jina AI embedding API.

        Args:
            contents: List of text strings to embed
            task_type: Type of embedding task (retrieval-query)

        Returns:
            List of ContentEmbedding objects
        """

        return await EmbedService._jina_embed_request(
            contents=contents,
            task_type="retrieval.query",
        )

    @staticmethod
    async def _jina_embed_request(
        contents: List[str],
        task_type: str = "retrieval.passage",
        late_chunking: bool = False,
        truncate: bool = False,
    ) -> List[List[float]]:
        """
        Internal method to embed text using Jina AI.
        This method is used by the public methods below.
        """
        if not contents:
            return []

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.JINA_API_KEY}",
        }

        batch_size = 100
        all_embeddings = []

        try:
            async with aiohttp.ClientSession() as session:
                for i in range(0, len(contents), batch_size):
                    batch = contents[i : i + batch_size]

                    if settings.JINA_EMBEDDING_MODEL == "jina-embeddings-v4":
                        formatted_input = [{"text": text} for text in batch]
                        batch = formatted_input

                    payload = {
                        "model": settings.JINA_EMBEDDING_MODEL,
                        "task": task_type,
                        "late_chunking": late_chunking,
                        "truncate": truncate,
                        "dimensions": settings.EMBEDDING_DIMENSION,
                        "input": batch,
                    }

                    async with session.post(
                        url=settings.JINA_EMBEDDING_URL,
                        json=payload,
                        headers=headers,
                    ) as response:
                        if response.status == 200:
                            result_data = await response.json()
                            result = result_data.get("data", [])
                            for embedding_data in result:
                                if embedding_data.get("embedding"):
                                    all_embeddings.append(embedding_data["embedding"])

                        else:
                            error_text = await response.text()
                            logger.error(
                                f"Jina API error {response.status}: {error_text}"
                            )
                            raise RuntimeError(
                                f"Jina API error {response.status}: {error_text}"
                            )

        except Exception as e:
            logger.error(f"Failed to embed text with Jina AI: {str(e)}")
            raise RuntimeError(f"Failed to embed text with Jina AI: {str(e)}")

        return all_embeddings
