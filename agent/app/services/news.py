from typing import List

from app.models.news.news import News
from app.models.news.news_schema import CreateNews, UpdateNews



class NewsService:
    @staticmethod
    async def get_news(news_id: str) -> News | None:
        return await News.find_one(News.id == news_id)


    @staticmethod
    async def create_news(news_data: CreateNews) -> News:
        news = News(**news_data.model_dump())
        await news.insert()
        return news

    @staticmethod
    async def create_multiple_news(news_data: List[CreateNews]) -> List[News]:
        news = [News(**news_data.model_dump()) for news_data in news_data]
        await News.insert_many(news)
        return news

    @staticmethod
    async def update_news(news_id: str, update_data: UpdateNews | dict) -> News | None:
        """
        Update a news document. Accepts either an UpdateNews model or a plain dict.
        This makes it convenient for callers that already have a dict of updates.
        """
        news = await News.find_one(News.id == news_id)
        if news:
            # Normalize update_data into a dict whether caller passed a model or dict
            if isinstance(update_data, dict):
                update_dict = {k: v for k, v in update_data.items() if v is not None}
            else:
                update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)

            for k, v in update_dict.items():
                setattr(news, k, v)
            await news.save()
        return news
    
    @staticmethod
    async def delete_news(news_id: str) -> bool:
        news = await News.find_one(News.id == news_id)
        if news:
            await news.delete()
            return True
        return False

    @staticmethod
    async def get_all_news() -> List[News]:
        return await News.find().to_list()
    

    @staticmethod
    async def get_latest_news() -> News | None:
        return await News.find().sort(-News.time).limit(1).to_list()