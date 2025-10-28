from app.apis.chat import router as chat_router
from app.apis.news import router as news_router


__all__ = [
    "chat_router",
    "news_router",
]

api_routers = [
    chat_router,
    news_router
]
