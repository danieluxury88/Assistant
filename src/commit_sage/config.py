from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from commit_sage.models import AppConfig


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = ""
    commit_sage_model: str = "claude-haiku-4-5-20251001"
    commit_sage_max_diff_lines: int = 300
    commit_sage_commit_style: str = "conventional"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def get_app_config() -> AppConfig:
    s = get_settings()
    return AppConfig(
        ai_provider="anthropic",
        api_model=s.commit_sage_model,
        commit_style=s.commit_sage_commit_style,
        max_diff_lines=s.commit_sage_max_diff_lines,
        ignored_patterns=[
            "*.lock",
            "*.min.js",
            "*.min.css",
            "package-lock.json",
            "yarn.lock",
            "composer.lock",
        ],
    )
