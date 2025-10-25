import asyncio
from typing import List

from app.services.chunk import ChunkService
from app.services.embed import EmbedService
from app.services.vectordb import VectorDatabaseService
from app.services.scrape import ScrapeService
from app.services.news import NewsService
from app.models.news.news_schema import CreateNews
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RAGService:
    """
    RAG Service for processing files and performing similarity searches.
    """

    @staticmethod
    async def process_news() -> bool:
        """
        Complete news processing pipeline:
        1. Scrape news from TradingView
        2. Save new news to database
        3. Chunk descriptions
        4. Generate embeddings
        5. Store in vector database

        Returns:
            bool: True if processing successful, False otherwise
        """
        try:
            logger.info("Starting news processing pipeline")

            # Step 1: Scrape news (without saving to DB in scrape service)
            scraped_news = await ScrapeService.scrape_news()
            if not scraped_news:
                logger.info("No new news found")
                return True

            logger.info(f"Scraped {len(scraped_news)} new articles")

            # Step 2: Save to database
            saved_count = await RAGService._save_news_to_database(scraped_news)
            logger.info(f"Saved {saved_count} articles to database")

            # Step 3-5: Process each news article with concurrency control
            success_count = await RAGService._process_news_batch(scraped_news)

            logger.info(
                f"Successfully processed {success_count}/{len(scraped_news)} articles"
            )
            return success_count > 0

        except Exception as e:
            logger.error(f"Error in news processing pipeline: {e}")
            return False

    @staticmethod
    async def _save_news_to_database(news_list: List[dict]) -> int:
        """Save news articles to database."""
        try:
            news_objects = []
            for news_data in news_list:
                try:
                    create_news = CreateNews(
                        id=news_data["id"],
                        title=news_data["title"],
                        time=news_data["time"],
                        source=news_data["source"],
                        description=news_data["description"],
                        VDB_added_at=None,
                    )
                    news_objects.append(create_news)
                except Exception as e:
                    logger.error(f"Error creating news object: {e}")
                    continue

            if news_objects:
                await NewsService.create_multiple_news(news_objects)
                return len(news_objects)
            return 0
        except Exception as e:
            logger.error(f"Error saving news to database: {e}")
            return 0

    @staticmethod
    async def _process_news_batch(
        news_list: List[dict], max_concurrent: int = 3
    ) -> int:
        """
        Process news articles with controlled concurrency to avoid overwhelming the vector DB.

        Args:
            news_list: List of news items to process
            max_concurrent: Maximum number of concurrent processing tasks

        Returns:
            Number of successfully processed articles
        """
        success_count = 0
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(news_item):
            async with semaphore:
                try:
                    result = await RAGService._process_single_news(news_item)
                    if result:
                        return 1
                except Exception as e:
                    logger.error(
                        f"Error processing news {news_item.get('id', 'unknown')}: {e}"
                    )
                return 0

        # Process all news items concurrently but with limited concurrency
        tasks = [process_with_semaphore(news_item) for news_item in news_list]
        results = await asyncio.gather(*tasks)
        success_count = sum(results)

        return success_count

    @staticmethod
    async def _process_single_news(news_item: dict) -> bool:
        """Process a single news article: chunk, embed, and store in vector DB."""
        try:
            news_id = news_item["id"]
            description = news_item["description"]

            if not description or not description.strip():
                logger.warning(f"Empty description for news {news_id}")
                return False

            # Step 1: Chunk the description
            chunks = await ChunkService.chunk_text(description)
            if not chunks:
                logger.error(f"Failed to chunk news {news_id}")
                return False

            # Step 2: Generate embeddings
            embeddings = await EmbedService.embed_text_jina(chunks)
            if not embeddings:
                logger.error(f"Failed to embed news {news_id}")
                return False

            # Step 3: Prepare payloads and store in vector DB
            payloads = []
            for i, chunk in enumerate(chunks):
                payload = {
                    "news_id": news_id,
                    "source": news_item["source"],
                    "title": news_item["title"],
                    "publish_date": news_item["time"].isoformat(),
                    "chunk_index": i,
                    "chunk_text": chunk,
                }
                payloads.append(payload)

            # Store vectors with smaller batches to reduce lock time
            batch_size = 10  # Process in smaller batches
            for i in range(0, len(embeddings), batch_size):
                batch_embeddings = embeddings[i : i + batch_size]
                batch_payloads = payloads[i : i + batch_size]

                vector_ids = await VectorDatabaseService.add_vectors(
                    vectors=batch_embeddings,
                    payloads=batch_payloads,
                )

                if not vector_ids:
                    logger.error(
                        f"Failed to store batch {i // batch_size + 1} for news {news_id}"
                    )
                    return False

                # Small delay to allow other operations
                await asyncio.sleep(0.01)

            # Update news to mark as added to VDB
            await NewsService.update_news(news_id, {"VDB_added_at": news_item["time"]})
            logger.info(
                f"Successfully processed news {news_id} with {len(chunks)} chunks"
            )
            return True

        except Exception as e:
            logger.error(f"Error processing single news: {e}")
            return False

    @staticmethod
    async def process_unprocessed_news() -> bool:
        """
        Process news articles that are in the database but not yet in vector DB.
        Useful for resuming interrupted processing.

        Returns:
            bool: True if processing successful, False otherwise
        """
        try:
            # Get all news that haven't been added to vector DB
            all_news = await NewsService.get_all_news()
            unprocessed_news = [news for news in all_news if news.VDB_added_at is None]

            if not unprocessed_news:
                logger.info("No unprocessed news found")
                return True

            logger.info(f"Found {len(unprocessed_news)} unprocessed news articles")

            # Convert to dict format and process with batch method
            news_dicts = []
            for news in unprocessed_news:
                news_dict = {
                    "id": news.id,
                    "title": news.title,
                    "time": news.time,
                    "source": news.source,
                    "description": news.description,
                }
                news_dicts.append(news_dict)

            success_count = await RAGService._process_news_batch(news_dicts)

            logger.info(
                f"Successfully processed {success_count}/{len(unprocessed_news)} unprocessed articles"
            )
            return success_count > 0

        except Exception as e:
            logger.error(f"Error processing unprocessed news: {e}")
            return False
