# ABC Dashboard settings — loaded from environment / .env

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    app_name: str = "ABC Compliance Platform"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://localhost:5432/abc_dashboard"
    redis_url: str = "redis://localhost:6379/0"

    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    allowed_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
