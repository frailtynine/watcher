from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core import settings
from app.db import engine
from app.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Cleanup on shutdown
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
