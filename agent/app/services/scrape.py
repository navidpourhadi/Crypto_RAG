import asyncio
import json
from datetime import datetime
from typing import List

import aiohttp
from bs4 import BeautifulSoup

from app.services.news import NewsService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ScrapeService:
    """
    Service class for Chunking text and PDF files.
    """

    @staticmethod
    async def scrape_news(use_id_filtering: bool = False) -> List[dict]:
        """
        Scrape crypto news from TradingView website using async requests.
        Uses timestamp-based filtering or ID-based filtering to avoid duplicates.

        Args:
            use_id_filtering: If True, uses ID-based duplicate checking instead of timestamp filtering

        Returns:
            List of dictionaries containing news data
        """
        base_url = "https://www.tradingview.com"
        url = "https://www.tradingview.com/news/markets/?category=crypto"

        # Get the latest news timestamp from database to avoid duplicates
        latest_news_time = await NewsService.get_latest_news()
        if len(latest_news_time) > 0:
            latest_news_time = latest_news_time[0].time
            logger.info(f"Latest news in database: {latest_news_time}")
        else:
            latest_news_time = None
            logger.info("No news found in database")

        async with aiohttp.ClientSession() as session:
            try:
                # Get main page with news list
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(
                            f"Failed to retrieve data from {url}. Status code: {response.status}"
                        )
                        return []

                    content = await response.text()
                    soup = BeautifulSoup(content, "html.parser")

                    # Find the JSON data containing news
                    script_tags = soup.find_all(
                        "script", {"type": "application/prs.init-data+json"}
                    )
                    target_json_data = None

                    for script_tag in script_tags:
                        if (
                            script_tag.string
                            and '{"title":"Market news"' in script_tag.string
                        ):
                            target_json_data = script_tag.string.strip()
                            break

                    if not target_json_data:
                        logger.warning(
                            'Script tag with {"title": "Market news"} not found.'
                        )
                        return []

                    # Parse JSON data
                    data_dict = json.loads(target_json_data)

                    # Extract news items
                    news_items = []
                    for key in data_dict:
                        if "blocks" in data_dict[key] and data_dict[key]["blocks"]:
                            for block in data_dict[key]["blocks"]:
                                if "news" in block and "items" in block["news"]:
                                    news_items.extend(block["news"]["items"])

                    if not news_items:
                        logger.info("No news items found on the page.")
                        return []

                    logger.info(f"Found {len(news_items)} total news items.")

                    # Process news items concurrently
                    tasks = []
                    for news_item in news_items:
                        task = ScrapeService._fetch_news_details(
                            session, base_url, news_item
                        )
                        tasks.append(task)

                    # Execute all tasks concurrently with a semaphore to limit concurrent requests
                    semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent requests
                    results = await asyncio.gather(
                        *[
                            ScrapeService._fetch_with_semaphore(semaphore, task)
                            for task in tasks
                        ],
                        return_exceptions=True,
                    )

                    # Filter successful results
                    scraped_news = []
                    for result in results:
                        if isinstance(result, dict) and result is not None:
                            # Parse the time string to datetime
                            try:
                                news_time = datetime.fromisoformat(
                                    result["time"].replace("Z", "+00:00")
                                )
                                result["time"] = news_time  # Store as datetime object
                                scraped_news.append(result)
                            except (ValueError, TypeError) as e:
                                logger.warning(
                                    f"Failed to parse time for news {result.get('title', 'unknown')}: {e}"
                                )
                                continue
                        elif isinstance(result, Exception):
                            logger.error(f"Error processing news item: {result}")

                    logger.info(f"Successfully scraped {len(scraped_news)} articles.")

                    # Apply filtering based on the chosen method
                    if use_id_filtering:
                        # Use ID-based filtering (more reliable but slower)
                        new_news = await ScrapeService._filter_existing_news(
                            scraped_news
                        )
                        logger.info(
                            f"Found {len(new_news)} new articles after ID-based filtering."
                        )
                    else:
                        # Use timestamp-based filtering (faster but less reliable)
                        new_news = []
                        for news_item in scraped_news:
                            if (
                                latest_news_time is None
                                or news_item["time"] > latest_news_time
                            ):
                                new_news.append(news_item)
                        logger.info(
                            f"Found {len(new_news)} new articles after timestamp filtering."
                        )

                    return new_news

            except Exception as e:
                logger.error(f"Error scraping news: {e}")
                return []

    @staticmethod
    async def _check_news_exists(news_id: str) -> bool:
        """
        Check if a news article with the given ID already exists in the database.

        Args:
            news_id: The news article ID to check

        Returns:
            True if the news exists, False otherwise
        """
        try:
            existing_news = await NewsService.get_news(news_id)
            return existing_news is not None
        except Exception as e:
            logger.error(f"Error checking if news exists: {e}")
            return False

    @staticmethod
    async def _filter_existing_news(news_list: List[dict]) -> List[dict]:
        """
        Filter out news articles that already exist in the database.

        Args:
            news_list: List of news dictionaries

        Returns:
            List of news dictionaries that don't exist in database
        """
        new_news = []
        for news_item in news_list:
            try:
                if not await ScrapeService._check_news_exists(news_item["id"]):
                    new_news.append(news_item)
                else:
                    logger.debug(f"News already exists: {news_item['title']}")
            except Exception as e:
                logger.error(f"Error checking news existence: {e}")
                continue

        return new_news

    @staticmethod
    async def _fetch_with_semaphore(semaphore: asyncio.Semaphore, coro):
        """Execute coroutine with semaphore to limit concurrent requests."""
        async with semaphore:
            return await coro

    @staticmethod
    async def _fetch_news_details(
        session: aiohttp.ClientSession, base_url: str, news_item: dict
    ) -> dict:
        """
        Fetch detailed content for a single news item.

        Args:
            session: aiohttp session
            base_url: Base URL for the website
            news_item: News item dictionary from the main page

        Returns:
            Dictionary containing full news data
        """
        try:
            story_url = base_url + news_item["storyPath"]

            async with session.get(story_url) as response:
                if response.status != 200:
                    logger.warning(
                        f"Failed to fetch story from {story_url}. Status: {response.status}"
                    )
                    return None

                content = await response.text()
                soup = BeautifulSoup(content, "html.parser")

                # Extract time
                time_element = soup.find("time")
                time = time_element["datetime"] if time_element else ""

                # Extract description
                description = ""
                story_container = soup.find("div", {"class": "js-news-story-container"})
                if story_container:
                    paragraphs = story_container.find_all("p")
                    description = "\n\n".join(
                        [
                            p.get_text().strip()
                            for p in paragraphs
                            if p.get_text().strip()
                        ]
                    )

                news_data = {
                    "id": news_item["id"],
                    "title": news_item["title"],
                    "time": time,
                    "source": news_item["source"],
                    "description": description,
                }

                logger.debug(f"Successfully processed: {news_item['title']}")
                return news_data

        except Exception as e:
            logger.error(
                f"Error fetching details for {news_item.get('title', 'unknown')}: {e}"
            )
            return None
