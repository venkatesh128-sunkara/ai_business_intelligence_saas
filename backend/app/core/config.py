from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "InsightIQ"
    API_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database: SQLite by default, switch to PostgreSQL via DATABASE_URL
    # e.g. postgresql+psycopg://user:pass@localhost:5432/bi_saas
    DATABASE_URL: str = "sqlite:///./bi_saas.db"

    # Auth
    SECRET_KEY: str = "change-me-in-production-please-use-a-random-64-char-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # LLM (OpenAI-compatible). Leave OPENAI_API_KEY empty to use the built-in
    # rule-based NL2SQL fallback engine.
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Upload limits
    MAX_UPLOAD_MB: int = 50
    MAX_ROWS_PER_DATASET: int = 200_000

    # Subscription limits per plan
    FREE_QUERIES_PER_MONTH: int = 500
    FREE_DATASETS: int = 10
    FREE_STORAGE_MB: int = 100

    # Storage
    UPLOAD_DIR: str = "./storage/uploads"

    # Admin bootstrap
    ADMIN_EMAIL: str = "admin@insightiq.dev"
    ADMIN_PASSWORD: str = "admin123"

    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
