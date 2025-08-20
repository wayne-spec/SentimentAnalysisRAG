from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    APP_ENV: str = "local"
    LOG_LEVEL: str = "INFO"

    SUPABASE_URL: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None

    ANALYZE_SHARED_SECRET: str = "change-me"  # Edge Function -> FastAPI

    EMBEDDINGS_PROVIDER: str | None = None
    OPENAI_API_KEY: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()