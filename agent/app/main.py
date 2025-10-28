from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.core.vectordb import VectorDatabase
from app.core.mongodb import MongoDatabase
from app.models.news.news import News
from app.models.chats.chat import Chat
from app.apis.chat import router as chat_router
from app.apis.news import router as news_router

from app.services.rag import RAGService

from app.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Global scheduler instance
scheduler = None

async def background_rag_task():
    """
    Background task to process cryptocurrency news.
    Runs the complete RAG pipeline: scrape, chunk, embed, and store.
    """
    try:
        logger.info("Starting background RAG news processing task")
        success = await RAGService.process_news()
        if success:
            logger.info("Background RAG task completed successfully")
        else:
            logger.warning("Background RAG task completed with some issues")
    except Exception as e:
        logger.error(f"Background RAG task failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles resource initialization and cleanup.
    """
    global scheduler
    
    logger.info("Starting application initialization")

    # Initialize databases
    app.state.vector_db_client = await VectorDatabase.get_client()
    logger.info("Vector Database initialized successfully")

    document_models = [News, Chat]  # Add your models here
    await MongoDatabase.initialize(document_models)
    logger.info("MongoDB initialized successfully")

    # Initialize and start background RAG scheduler
    try:
        scheduler = AsyncIOScheduler()
        
        # Add RAG processing job with configurable interval
        scheduler.add_job(
            background_rag_task,
            trigger=IntervalTrigger(hours=settings.RAG_PROCESSING_INTERVAL_HOURS),
            id="rag_news_processing",
            name="Cryptocurrency News RAG Processing",
            replace_existing=True,
            max_instances=1,  # Prevent overlapping executions
            coalesce=True,    # If missed, run once when available
        )
        
        # Start the scheduler
        scheduler.start()
        logger.info(f"Background RAG scheduler started successfully (runs every {settings.RAG_PROCESSING_INTERVAL_HOURS} hour(s))")
        
        # Run initial RAG processing on startup if configured
        if settings.RAG_RUN_ON_STARTUP:
            logger.info("Running initial RAG processing on startup...")
            await background_rag_task()
        else:
            logger.info("Skipping initial RAG processing (disabled in config)")
        
    except Exception as e:
        logger.error(f"Failed to initialize background RAG scheduler: {e}")

    logger.info("Application startup completed")
    yield

    # Cleanup resources
    logger.info("Starting application cleanup")
    if scheduler:
        try:
            scheduler.shutdown(wait=False)
            logger.info("Background RAG scheduler shutdown successfully")
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}")


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
    return {
        "message": "Cryptocurrency Market Analysis Agent API",
        "status": "running",
        "features": [
            "Real-time news scraping from TradingView",
            "RAG-powered market analysis",
            "Background news processing",
            "Intelligent cryptocurrency insights"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": "2025-10-27"}

@app.get("/rag/status")
async def rag_status():
    """Get RAG background processing status."""
    global scheduler
    
    if not scheduler:
        return {"status": "scheduler_not_initialized"}
    
    try:
        jobs = scheduler.get_jobs()
        rag_job = next((job for job in jobs if job.id == "rag_news_processing"), None)
        
        if rag_job:
            return {
                "status": "active",
                "job_id": rag_job.id,
                "job_name": rag_job.name,
                "next_run": rag_job.next_run_time.isoformat() if rag_job.next_run_time else None,
                "trigger": str(rag_job.trigger),
                "max_instances": rag_job.max_instances,
            }
        else:
            return {"status": "job_not_found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/rag/trigger")
async def trigger_rag_processing():
    """Manually trigger RAG processing."""
    try:
        logger.info("Manual RAG processing triggered via API")
        success = await RAGService.process_news()
        return {
            "status": "completed",
            "success": success,
            "message": "RAG processing completed successfully" if success else "RAG processing completed with issues"
        }
    except Exception as e:
        logger.error(f"Manual RAG processing failed: {e}")
        return {"status": "error", "message": str(e)}


app.include_router(news_router, prefix="/api", tags=["News"])

app.include_router(chat_router, prefix="/api", tags=["Chat"])
