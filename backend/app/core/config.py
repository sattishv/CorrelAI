"""
------------------------------------------------------------------------------
CorrelAI

Configuration Module

This module contains all application configuration settings.

------------------------------------------------------------------------------
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Global application settings.
    """

    app_name: str = "CorrelAI"

    version: str = "0.1.0"

    environment: str = "development"

    debug: bool = True

    api_prefix: str = "/api/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings object.
    """
    return Settings()


settings = get_settings()