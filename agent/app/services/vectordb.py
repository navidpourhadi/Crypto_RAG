import uuid
from typing import Any, Dict, List

from qdrant_client.models import (
    Batch,
    FieldCondition,
    Filter,
    MatchValue,
    ScoredPoint,
)

from app.core.config import settings
from app.core.vectordb import VectorDatabase

from app.utils.logger import get_logger

logger = get_logger(__name__)

class VectorDatabaseService:
    """
    Service class for handling vector database operations.

    Controlling the flow of data through the vector database:
    
    1. Add Vectors
    2. Search Vectors
    3. Delete Vectors
    4. Get Vectors
    5. Count Vectors

    6. processing the news to add their vectors to the vector database
    
    """

    @staticmethod
    async def add_vectors(
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]] | None = None,
        point_ids: List[str | uuid.UUID | int] | None = None,
    ) -> List[str]:
        """
        Add multiple vectors to the collection in batch.

        Args:
            vectors: List of vector data to add
            payloads: Optional list of metadata for each vector
            point_ids: Optional list of custom IDs, auto-generated uuid if None

        Returns:
            List of IDs of the added vectors
        """
        # Generate IDs if not provided
        if point_ids is None:
            point_ids = [str(uuid.uuid4()) for _ in vectors]

        # Ensure payloads list matches vectors length
        if payloads is None:
            payloads = [{} for _ in vectors]

        # Ensure lengths match
        if len(vectors) != len(payloads) or len(vectors) != len(point_ids):
            raise ValueError(
                "Vectors, payloads, and point_ids must have the same length"
            )

        client = await VectorDatabase.get_client()

        result = await client.upsert(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points=Batch(
                ids=point_ids,
                vectors=vectors,
                payloads=payloads,
            ),
        )
        return result

    @staticmethod
    async def search_vectors(
        query_vector: List[float],
        limit: int = settings.VECTOR_SEARCH_TOP_K,
        score_threshold: float | None = None,
        filter_conditions: Dict[str, Any] | None = None,
    ) -> list[dict]:
        """
        Search for similar vectors in the collection.

        Args:
            query_vector: Vector to search for
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score threshold
            filter_conditions: Optional metadata filters

        Returns:
            List of scored points with similarity scores
        """
        client = await VectorDatabase.get_client()

        # Build filter if conditions provided
        query_filter = None
        if filter_conditions:
            conditions = []
            for field, value in filter_conditions.items():
                conditions.append(
                    FieldCondition(key=field, match=MatchValue(value=value))
                )
            query_filter = Filter(must=conditions)

        response = await client.search(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter,
        )
        result = [{**hit.payload, "score": hit.score} for hit in response]
        return result

    @staticmethod
    async def delete_vectors(point_ids: List[str]) -> bool:
        """
        Delete multiple vectors by their IDs.

        Args:
            point_ids: List of vector IDs to delete

        Returns:
            True if all deleted successfully, False otherwise
        """
        client = await VectorDatabase.get_client()

        try:
            await client.delete(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points_selector=point_ids,
            )
            return True
        except Exception:
            return False

    @staticmethod
    async def get_vector(
        point_id: List[str | uuid.UUID | int],
        with_payload: bool = True,
        with_vectors: bool = False,
    ) -> list[ScoredPoint] | None:
        """
        Retrieve a specific vector by ID.

        Args:
            point_id: ID of the vector to retrieve

        Returns:
            ScoredPoint if found, None otherwise
        """
        client = await VectorDatabase.get_client()

        try:
            results = await client.retrieve(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                ids=point_id,
                with_payload=with_payload,
                with_vectors=with_vectors,
            )
            return results[0] if results else None
        except Exception:
            return None

    @staticmethod
    async def count_vectors(
        filter_conditions: Dict[str, Any] | None = None,
    ) -> int:
        """
        Count vectors in the collection, optionally with filter.

        Args:
            filter_conditions: Optional metadata filters

        Returns:
            Number of vectors matching the conditions
        """
        client = await VectorDatabase.get_client()

        # Build filter if conditions provided
        count_filter = None
        if filter_conditions:
            conditions = []
            for field, value in filter_conditions.items():
                conditions.append(
                    FieldCondition(key=field, match=MatchValue(value=value))
                )
            count_filter = Filter(must=conditions)

        result = await client.count(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            count_filter=count_filter,
        )

        return result.count


