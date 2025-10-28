from app.agent.tools.news import (
    search_news_rag
)

news_tools = [
    search_news_rag
]


all_tools = [
    *news_tools,
]

__all__ = [
    "search_news_rag",
    "rag_tools",
    "all_tools",
]
