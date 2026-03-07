"""Parse and compact Git diff output for AI consumption."""

from dataclasses import dataclass


@dataclass
class FileDiff:
    path: str
    added: int
    removed: int
    hunks: list[str]


def parse_diff(diff_text: str) -> list[FileDiff]:
    """Parse raw git diff output into FileDiff objects."""
    file_diffs: list[FileDiff] = []
    current_path: str | None = None
    current_hunks: list[str] = []
    current_hunk_lines: list[str] = []
    added = 0
    removed = 0

    def flush_hunk():
        if current_hunk_lines:
            current_hunks.append("\n".join(current_hunk_lines))
            current_hunk_lines.clear()

    def flush_file():
        nonlocal added, removed
        if current_path is not None:
            flush_hunk()
            file_diffs.append(FileDiff(
                path=current_path,
                added=added,
                removed=removed,
                hunks=list(current_hunks),
            ))
            current_hunks.clear()
            added = 0
            removed = 0

    for line in diff_text.splitlines():
        if line.startswith("diff --git"):
            flush_file()
            current_path = None
        elif line.startswith("+++ b/"):
            current_path = line[6:].strip()
        elif line.startswith("--- "):
            continue
        elif line.startswith("@@ "):
            flush_hunk()
            current_hunk_lines.append(line)
        elif current_path and line.startswith("+") and not line.startswith("+++"):
            added += 1
            current_hunk_lines.append(line)
        elif current_path and line.startswith("-") and not line.startswith("---"):
            removed += 1
            current_hunk_lines.append(line)
        elif current_path:
            current_hunk_lines.append(line)

    flush_file()
    return file_diffs


def compact_diff(diff_text: str, max_lines: int = 300) -> str:
    """
    Return a compacted version of the diff, trimmed to max_lines.
    Prioritizes files with more changes.
    """
    if not diff_text.strip():
        return ""

    file_diffs = parse_diff(diff_text)
    if not file_diffs:
        return diff_text[:max_lines * 80]  # fallback: raw truncation

    # Sort by most changed lines first
    file_diffs.sort(key=lambda f: f.added + f.removed, reverse=True)

    lines_used = 0
    sections: list[str] = []

    for fd in file_diffs:
        header = f"--- {fd.path} (+{fd.added}/-{fd.removed})"
        hunk_text = "\n".join(fd.hunks)
        hunk_lines = hunk_text.splitlines()

        if lines_used + len(hunk_lines) + 1 > max_lines:
            remaining = max_lines - lines_used - 2
            if remaining > 0:
                trimmed = hunk_lines[:remaining]
                sections.append(header)
                sections.append("\n".join(trimmed))
                sections.append(f"... [{len(hunk_lines) - remaining} more lines trimmed]")
            break

        sections.append(header)
        sections.append(hunk_text)
        lines_used += len(hunk_lines) + 1

    return "\n".join(sections)


def count_diff_stats(diff_text: str) -> tuple[int, int]:
    """Return (total_added, total_removed) for the diff."""
    added = sum(1 for line in diff_text.splitlines() if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff_text.splitlines() if line.startswith("-") and not line.startswith("---"))
    return added, removed
