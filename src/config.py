# ABC Dashboard settings — loaded from environment / .env

from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    app_name: str = "ABC Compliance Platform"
    debug: bool = False

    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    secret_key: str
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    allowed_origins: list[str] = ["http://localhost:5173"]

    @field_validator("secret_key")
    @classmethod
    def _secret_key_not_default(cls, v: str) -> str:
        if v == "change-me-in-production":
            raise ValueError(
                "SECRET_KEY is set to the default value. "
                "Set a strong secret in .env or environment."
            )
        return v


settings = Settings()  # type: ignore[call-arg]  # loaded from env/.env by pydantic-settings
