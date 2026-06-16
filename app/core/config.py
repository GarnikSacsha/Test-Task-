from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Tempail Scraper API"
    app_env: Literal["local", "test", "production"] = "local"
    log_level: str = "INFO"

    tempail_url: str = "https://tempail.com/ua/"
    browser_headless: bool = True
    browser_timeout_ms: int = 30_000
    browser_slow_mo_ms: int = 0
    inbox_poll_interval_ms: int = 1_000
    inbox_poll_attempts: int = 3

    api_request_timeout_seconds: int = 45
    cors_origins: str = "*"

    demo_mode: bool = False

    @field_validator("*", mode="before")
    @classmethod
    def strip_env_strings(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
