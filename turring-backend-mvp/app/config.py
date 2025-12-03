"""Application configuration using Pydantic Settings."""

import os
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    # OpenAI Configuration
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 10.0
    llm_temperature: float = 0.85

    # Humanization Settings
    llm_max_words: int = 18
    humanize_typo_rate: float = 0.22
    humanize_max_typos: int = 2
    humanize_min_delay: float = 0.8
    humanize_max_delay: float = 2.5

    # Game Configuration
    round_limit_secs: int = 300  # 5 minutes
    turn_limit_secs: int = 30
    score_correct: int = 100
    score_wrong: int = -200
    score_timeout_win: int = 100

    # Matchmaking
    h2h_prob: float = 0.5  # Probability of human-to-human matching
    match_window_secs: float = 10.0

    # Application
    app_env: str = "dev"
    app_version: str = "2"

    # CORS
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Redis (optional)
    redis_url: str = "redis://localhost:6379/0"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()
