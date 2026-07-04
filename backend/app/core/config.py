from functools import lru_cache
import os

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "PulseQueue"
    environment: str = os.getenv("ENVIRONMENT", "development")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./pulsequeue.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    jwt_issuer: str = os.getenv("JWT_ISSUER", "pulsequeue")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    worker_heartbeat_timeout_seconds: int = int(os.getenv("WORKER_HEARTBEAT_TIMEOUT_SECONDS", "60"))
    default_page_size: int = int(os.getenv("DEFAULT_PAGE_SIZE", "25"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()

