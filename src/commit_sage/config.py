from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from commit_sage.models import AppConfig

SUPPORTED_AI_PROVIDERS = {"anthropic", "openai"}
DEFAULT_MODELS = {
    "anthropic": "claude-haiku-4-5-20251001",
    "openai": "gpt-5-mini",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    openai_base_url: str = ""
    commit_sage_provider: str = ""
    commit_sage_model: str = ""
    commit_sage_max_diff_lines: int = 300
    commit_sage_commit_style: str = "conventional"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def resolve_ai_provider(
    settings: Settings | None = None,
    *,
    require_credentials: bool = False,
) -> str:
    s = settings or get_settings()

    provider = s.commit_sage_provider.strip().lower()
    if provider:
        if provider not in SUPPORTED_AI_PROVIDERS:
            supported = ", ".join(sorted(SUPPORTED_AI_PROVIDERS))
            raise ValueError(
                f"Unsupported COMMIT_SAGE_PROVIDER '{provider}'. "
                f"Expected one of: {supported}."
            )
        return provider

    if s.anthropic_api_key:
        return "anthropic"
    if s.openai_api_key:
        return "openai"

    if require_credentials:
        raise ValueError(
            "No supported API credentials detected. "
            "Set ANTHROPIC_API_KEY or OPENAI_API_KEY, or set COMMIT_SAGE_PROVIDER explicitly."
        )

    return "anthropic"


def resolve_model(
    provider: str,
    settings: Settings | None = None,
    override: str | None = None,
) -> str:
    if override:
        return override

    s = settings or get_settings()
    configured = s.commit_sage_model.strip()
    if configured:
        return configured

    try:
        return DEFAULT_MODELS[provider]
    except KeyError as e:
        raise ValueError(f"Unsupported AI provider '{provider}'.") from e


def get_app_config() -> AppConfig:
    s = get_settings()
    provider = resolve_ai_provider(s)
    return AppConfig(
        ai_provider=provider,
        api_model=resolve_model(provider, s),
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
