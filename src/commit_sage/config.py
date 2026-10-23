import os
import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import dotenv_values
from pydantic import BaseModel, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from commit_sage.models import AppConfig

SUPPORTED_AI_PROVIDERS = ("anthropic", "openai", "command")
DEFAULT_MODELS = {
    "anthropic": "claude-haiku-4-5-20251001",
    "openai": "gpt-5-mini",
}
DEFAULT_PROFILE = "claude"


def user_config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "commit-sage"


def env_files() -> tuple[Path, ...]:
    """User-level .env first, then the working directory's (later files win)."""
    return (user_config_dir() / ".env", Path(".env"))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    commit_sage_profile: str = ""
    commit_sage_model: str = ""
    commit_sage_config: str = ""
    commit_sage_max_diff_lines: int = 300
    commit_sage_commit_style: str = "conventional"


class Profile(BaseModel):
    """One way of reaching a model: an API billed per token, a local server, or a subscription CLI."""

    provider: Literal["anthropic", "openai", "command"]
    model: str | None = None
    # Name of the environment variable (or .env entry) holding the API key.
    api_key_env: str | None = None
    # Literal key, only for servers that ignore it (e.g. a local llama.cpp endpoint).
    api_key: str | None = None
    # OpenAI-compatible endpoint; leave empty for api.openai.com.
    base_url: str | None = None
    # For provider "command": argv that reads the prompt on stdin and prints the reply;
    # "{model}" in an argument is replaced by the resolved model.
    command: list[str] | None = None
    description: str = ""


BUILTIN_PROFILES = {
    "claude": Profile(
        provider="anthropic",
        api_key_env="ANTHROPIC_API_KEY",
        description="Anthropic API, billed per token",
    ),
    "openai": Profile(
        provider="openai",
        api_key_env="OPENAI_API_KEY",
        description="OpenAI API, billed per token",
    ),
}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def config_path(settings: Settings | None = None) -> Path:
    s = settings or get_settings()
    if s.commit_sage_config.strip():
        return Path(s.commit_sage_config.strip()).expanduser()
    return user_config_dir() / "config.toml"


def load_profiles(settings: Settings | None = None) -> tuple[str, dict[str, Profile]]:
    """Return the configured default profile name and all profiles (built-in plus config file)."""
    path = config_path(settings)
    profiles = dict(BUILTIN_PROFILES)
    if not path.is_file():
        return DEFAULT_PROFILE, profiles

    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"Invalid TOML in {path}: {e}") from e

    for name, raw in data.get("profiles", {}).items():
        try:
            profile = Profile(**raw)
        except ValidationError as e:
            raise ValueError(f"Invalid profile '{name}' in {path}: {e}") from e
        if profile.provider == "command" and not profile.command:
            raise ValueError(f"Profile '{name}' in {path} uses provider 'command' but has no 'command'.")
        profiles[name] = profile

    return data.get("default_profile", DEFAULT_PROFILE), profiles


def resolve_profile(
    settings: Settings | None = None,
    name: str | None = None,
) -> tuple[str, Profile]:
    """Pick a profile: explicit name, then COMMIT_SAGE_PROFILE, then the config file's default."""
    s = settings or get_settings()
    default, profiles = load_profiles(s)
    chosen = (name or s.commit_sage_profile or default).strip()
    if chosen not in profiles:
        available = ", ".join(sorted(profiles))
        raise ValueError(f"Unknown profile '{chosen}'. Available: {available}.")
    return chosen, profiles[chosen]


def resolve_model(
    profile: Profile,
    settings: Settings | None = None,
    override: str | None = None,
) -> str | None:
    """--model wins, then COMMIT_SAGE_MODEL, then the profile, then the provider default."""
    if override:
        return override
    s = settings or get_settings()
    if s.commit_sage_model.strip():
        return s.commit_sage_model.strip()
    return profile.model or DEFAULT_MODELS.get(profile.provider)


def env_value(name: str) -> str:
    """Read a variable from the process environment, falling back to the .env files."""
    if os.environ.get(name):
        return os.environ[name]
    value = ""
    for path in env_files():
        if path.is_file():
            value = dotenv_values(path).get(name) or value
    return value


def resolve_api_key(profile: Profile) -> str:
    if profile.api_key:
        return profile.api_key
    if profile.api_key_env:
        return env_value(profile.api_key_env)
    return ""


def get_app_config() -> AppConfig:
    s = get_settings()
    return AppConfig(
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
