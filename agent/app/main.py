from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.vectordb import VectorDatabase
from app.core.mongodb import MongoDatabase
from app.models.news.news import News
from app.models.chats.chat import Chat

from app.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles resource initialization and cleanup.
    """
    logger.info("Starting application initialization")

    app.state.vector_db_client = await VectorDatabase.get_client()
    logger.info("Vector Database initialized successfully")

    document_models = [News, Chat]  # Add your models here
    await MongoDatabase.initialize(document_models)
    logger.info("MongoDB initialized successfully")

    logger.info("Application startup completed")
    yield

    # Cleanup resources
    # logger.info("Starting application cleanup")


app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello": "World"}


# app.include_router(auth_router, prefix="/api", tags=["Authentication"])

# app.include_router(chat_router, prefix="/api", tags=["Chat"])

# app.include_router(user_router, prefix="/api", tags=["Users"])

# app.include_router(user_file_router, prefix="/api", tags=["Files"])

# app.include_router(device_router, prefix="/api", tags=["Devices"])

# app.include_router(ocr_router, prefix="/api", tags=["OCR"])
