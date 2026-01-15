from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)
    
    DATABASE_URL: str
    SECRET_KEY: str
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost"]
    ENVIRONMENT: str = "development"
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours


settings = Settings()
