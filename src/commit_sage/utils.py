"""Shared utility helpers."""

from pathlib import Path

from rich.console import Console

console = Console()


def find_dotenv(start: Path | None = None) -> Path | None:
    """Walk up from start looking for a .env file."""
    current = (start or Path.cwd()).resolve()
    for directory in [current, *current.parents]:
        candidate = directory / ".env"
        if candidate.is_file():
            return candidate
    return None


def truncate(text: str, max_chars: int = 200) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


def plural(n: int, singular: str, plural_form: str | None = None) -> str:
    p = plural_form or (singular + "s")
    return f"{n} {singular if n == 1 else p}"
