from typing import List

from fastapi.routing import APIRouter

from app.models.news.news_schema import NewsResponse
from app.services.news import NewsService

router = APIRouter(prefix="/news")

@router.get("/", response_model=List[NewsResponse])
async def get_news():
    """
    Get all news.
    """

    return await NewsService.get_all_news()
