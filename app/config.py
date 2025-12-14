from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-pro"
    max_file_size: int = 10 * 1024 * 1024  # 10MB default
    microsoft_tenant_id: str | None = None
    microsoft_client_id: str | None = None
    microsoft_client_secret: str | None = None
    microsoft_planner_container_url: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.development"), env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
