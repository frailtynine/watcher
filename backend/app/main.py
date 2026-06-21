from contextlib import asynccontextmanager
import logging
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core import settings
from app.db import engine
from app.api import api_router
from app.producers.rss import rss_producer_job
from app.producers.telegram_manager import telegram_manager_job
from app.ai.consumer import run_ai_consumer_job
from app.delivery.telegram.telegram_apps_manager import (
    telegram_apps_manager_job,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)

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
        trigger=IntervalTrigger(minutes=settings.RSS_FETCH_INTERVAL_MINUTES),
        id="rss_producer",
        name="RSS Feed Producer",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        run_ai_consumer_job,
        trigger=IntervalTrigger(minutes=1),
        id="ai_consumer",
        name="AI Consumer Job",
        replace_existing=True,
        max_instances=1,
    )
    telegram_manager_task = asyncio.create_task(
        telegram_manager_job(
            check_interval_seconds=settings.TELEGRAM_MANAGER_CHECK_INTERVAL_SECONDS
        )
    )
    app.state.telegram_manager_task = telegram_manager_task
    telegram_apps_task = asyncio.create_task(
        telegram_apps_manager_job(
            check_interval_seconds=(
                settings.TELEGRAM_APPS_MANAGER_CHECK_INTERVAL_SECONDS
            )
        )
    )
    app.state.telegram_apps_task = telegram_apps_task
    logger.info(
        f"Scheduled RSS producer job to run every "
        f"{settings.RSS_FETCH_INTERVAL_MINUTES} minutes"
    )

    yield

    # Cleanup on shutdown
    telegram_manager_task.cancel()
    telegram_apps_task.cancel()
    try:
        await telegram_manager_task
    except asyncio.CancelledError:
        logger.info("Telegram manager task cancelled successfully")
    try:
        await telegram_apps_task
    except asyncio.CancelledError:
        logger.info("Telegram apps task cancelled successfully")
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
