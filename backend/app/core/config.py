from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    DATABASE_URL: str
    SECRET_KEY: str
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    ENVIRONMENT: str = "development"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # RSS Producer Job Settings
    RSS_FETCH_INTERVAL_MINUTES: int = 1
    RSS_FETCH_CONCURRENCY: int = Field(default=50, gt=0)
    RSS_FETCH_TIMEOUT_SECONDS: float = Field(default=30, gt=0)
    RSS_JOB_TIMEOUT_SECONDS: float = Field(default=300, gt=0)
    OPEN_ROUTER_API_KEY: str = ""
    ENCRYPTION_KEY: str

    # Telegram Manager Settings
    TELEGRAM_MANAGER_CHECK_INTERVAL_SECONDS: int = 300
    TELEGRAM_APPS_MANAGER_CHECK_INTERVAL_SECONDS: int = 60


settings = Settings()
