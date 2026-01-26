from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core import settings
from app.db import engine
from app.api import api_router
from app.producers.rss import rss_producer_job

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler = AsyncIOScheduler()
    scheduler.start()
    app.state.scheduler = scheduler

    # Schedule RSS producer job
    scheduler.add_job(
        rss_producer_job,
        trigger=IntervalTrigger(
            minutes=settings.RSS_FETCH_INTERVAL_MINUTES
        ),
        id="rss_producer",
        name="RSS Feed Producer",
        replace_existing=True,
        max_instances=1
    )

    logger.info(
        f"Scheduled RSS producer job to run every "
        f"{settings.RSS_FETCH_INTERVAL_MINUTES} minutes"
    )

    yield

    # Cleanup on shutdown
    scheduler.shutdown(wait=True)
    await engine.dispose()


def get_app() -> FastAPI:
    """Application factory for creating FastAPI app instance."""
    application = FastAPI(
        title="NewsWatcher API",
        description="NewsWatcher Backend API with Authentication",
        version="0.1.0",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router, prefix="/api")

    @application.get("/")
    async def root():
        return {"message": "NewsWatcher API", "version": "0.1.0"}

    @application.get("/health")
    async def health():
        return {"status": "healthy"}

    return application


app = get_app()
