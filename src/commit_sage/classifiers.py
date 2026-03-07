from pathlib import Path
from fnmatch import fnmatch


# Maps file extension -> category label
EXTENSION_MAP: dict[str, str] = {
    # Python
    ".py": "python",
    ".pyi": "python",
    # PHP
    ".php": "php",
    # JavaScript / TypeScript
    ".js": "js",
    ".jsx": "js",
    ".ts": "ts",
    ".tsx": "ts",
    ".mjs": "js",
    ".cjs": "js",
    # CSS / SCSS / Less
    ".css": "css",
    ".scss": "css",
    ".sass": "css",
    ".less": "css",
    # YAML
    ".yml": "yaml",
    ".yaml": "yaml",
    # Markdown / docs
    ".md": "docs",
    ".rst": "docs",
    ".txt": "docs",
    # JSON
    ".json": "config",
    ".jsonc": "config",
    # TOML / INI / config
    ".toml": "config",
    ".ini": "config",
    ".cfg": "config",
    ".conf": "config",
    ".env": "config",
    # Templates
    ".html": "frontend",
    ".htm": "frontend",
    ".twig": "frontend",
    ".jinja": "frontend",
    ".jinja2": "frontend",
    # Assets
    ".png": "assets",
    ".jpg": "assets",
    ".jpeg": "assets",
    ".gif": "assets",
    ".svg": "assets",
    ".ico": "assets",
    ".webp": "assets",
    ".woff": "assets",
    ".woff2": "assets",
    ".ttf": "assets",
    # Shell
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    # SQL
    ".sql": "sql",
    # XML
    ".xml": "config",
    # Lock files (noise)
    ".lock": "lock",
}

# High-level area labels based on categories
AREA_MAP: dict[str, str] = {
    "python": "backend",
    "php": "backend",
    "js": "frontend",
    "ts": "frontend",
    "css": "frontend",
    "frontend": "frontend",
    "docs": "docs",
    "config": "config",
    "yaml": "config",
    "shell": "config",
    "sql": "backend",
    "assets": "assets",
    "lock": "noise",
}

# Patterns for noisy / generated files to deprioritize
NOISE_PATTERNS: list[str] = [
    "*.lock",
    "*.min.js",
    "*.min.css",
    "package-lock.json",
    "yarn.lock",
    "composer.lock",
    "*.generated.*",
    "*.map",
    "__pycache__/*",
    "*.pyc",
    ".env",
    "node_modules/*",
    "vendor/*",
]


def classify_file(path: str) -> str:
    """Return the category label for a file path."""
    ext = Path(path).suffix.lower()
    return EXTENSION_MAP.get(ext, "unknown")


def get_area(category: str) -> str:
    """Return high-level area for a category."""
    return AREA_MAP.get(category, "unknown")


def is_noisy(path: str) -> bool:
    """Return True if the file is considered low-value noise."""
    name = Path(path).name
    for pattern in NOISE_PATTERNS:
        if fnmatch(path, pattern) or fnmatch(name, pattern):
            return True
    return False


def categorize_files(paths: list[str]) -> dict[str, int]:
    """Return a count of files per category, excluding noise."""
    counts: dict[str, int] = {}
    for path in paths:
        if is_noisy(path):
            continue
        cat = classify_file(path)
        counts[cat] = counts.get(cat, 0) + 1
    return counts


def infer_scope(paths: list[str]) -> str | None:
    """
    Infer a conventional commit scope from changed files.
    Returns None if the scope is mixed or unclear.
    """
    areas: set[str] = set()
    for path in paths:
        if is_noisy(path):
            continue
        cat = classify_file(path)
        area = get_area(cat)
        if area not in ("noise", "unknown"):
            areas.add(area)

    if len(areas) == 1:
        area = areas.pop()
        # Try to get a more specific scope from the directory structure
        dirs = _common_directory(paths)
        if dirs:
            return dirs
        return area
    return None


def group_files_by_area(paths: list[str]) -> dict[str, list[str]]:
    """
    Group files by their high-level area, excluding noise.
    Returns a dict of area -> [file paths].
    """
    groups: dict[str, list[str]] = {}
    for path in paths:
        if is_noisy(path):
            continue
        cat = classify_file(path)
        area = get_area(cat)
        if area in ("noise",):
            continue
        if area == "unknown":
            area = "other"
        groups.setdefault(area, []).append(path)
    return groups


def is_mixed_changes(paths: list[str]) -> bool:
    """Return True if files span more than one meaningful area."""
    return len(group_files_by_area(paths)) > 1


def _common_directory(paths: list[str]) -> str | None:
    """
    If all paths share a common top-level directory (under src/ or similar),
    return that directory name as a potential scope.
    """
    top_dirs: set[str] = set()
    for path in paths:
        parts = Path(path).parts
        if len(parts) > 1:
            # Skip well-known root dirs that are too generic
            skip = {"src", "lib", "app", ".", "tests", "test"}
            first = parts[0]
            if first not in skip:
                top_dirs.add(first)
            elif len(parts) > 2:
                second = parts[1]
                if second not in skip:
                    top_dirs.add(second)

    if len(top_dirs) == 1:
        return top_dirs.pop()
    return None
