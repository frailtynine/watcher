from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core import settings
from app.db import Base, engine
from app.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Cleanup on shutdown
    await engine.dispose()


app = FastAPI(
    title="NewsWatcher API",
    description="NewsWatcher Backend API with Authentication",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "NewsWatcher API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
