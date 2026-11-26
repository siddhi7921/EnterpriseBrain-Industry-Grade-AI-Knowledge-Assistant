from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "EnterpriseBrain"
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "dev-only-secret-key-change-in-production-9f8e7d6c"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    FRONTEND_URL: str = "http://localhost:5173"

    DATABASE_URL: str = "sqlite+pysqlite:///./enterprisebrain_dev.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_TASK_ALWAYS_EAGER: bool = True

    STORAGE_BACKEND: str = "local"
    STORAGE_ENDPOINT: str = "http://localhost:9000"
    STORAGE_BUCKET: str = "enterprisebrain"
    STORAGE_ACCESS_KEY: str = "minioadmin"
    STORAGE_SECRET_KEY: str = "minioadmin"
    LOCAL_STORAGE_DIR: str = "./storage_data"

    EMBEDDING_PROVIDER: str = "local_hash"
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DIMENSION: int = 1024

    RERANKER_PROVIDER: str = "lexical"
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"

    LLM_PROVIDER: str = "extractive_fallback"
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"

    MAX_UPLOAD_SIZE_MB: int = 25
    RATE_LIMIT_CHAT_PER_MINUTE: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
