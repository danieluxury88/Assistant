"""Build compact, AI-ready summaries from Git change data."""

from pathlib import Path

from commit_sage.classifiers import categorize_files, infer_scope, is_noisy, classify_file
from commit_sage.diff_parser import compact_diff, count_diff_stats, parse_diff
from commit_sage.git_tools import FileStatus
from commit_sage.models import RepositoryChangeSummary


def build_summary(
    branch: str,
    staged_files: list[str],
    unstaged_files: list[str],
    staged_diff: str,
    unstaged_diff: str,
    max_diff_lines: int = 300,
) -> RepositoryChangeSummary:
    all_files = list({*staged_files, *unstaged_files})
    categories = categorize_files(all_files)
    scope = infer_scope(all_files)

    summary_text = _build_summary_text(
        branch=branch,
        staged_files=staged_files,
        unstaged_files=unstaged_files,
        staged_diff=staged_diff,
        unstaged_diff=unstaged_diff,
        max_diff_lines=max_diff_lines,
    )

    return RepositoryChangeSummary(
        branch=branch,
        staged_files=staged_files,
        unstaged_files=unstaged_files,
        file_categories=categories,
        inferred_scope=scope,
        summary_text=summary_text,
    )


def _build_summary_text(
    branch: str,
    staged_files: list[str],
    unstaged_files: list[str],
    staged_diff: str,
    unstaged_diff: str,
    max_diff_lines: int,
) -> str:
    parts: list[str] = []

    parts.append(f"Branch: {branch}")

    all_files = list({*staged_files, *unstaged_files})
    useful_files = [f for f in all_files if not is_noisy(f)]

    if useful_files:
        parts.append(f"\nChanged files ({len(useful_files)}):")
        for f in useful_files[:20]:
            cat = classify_file(f)
            parts.append(f"  [{cat}] {f}")
        if len(useful_files) > 20:
            parts.append(f"  ... and {len(useful_files) - 20} more")

    noisy = [f for f in all_files if is_noisy(f)]
    if noisy:
        parts.append(f"\n(Skipped {len(noisy)} generated/lock files)")

    # Staged diff takes priority
    if staged_diff.strip():
        added, removed = count_diff_stats(staged_diff)
        parts.append(f"\nStaged changes: +{added} -{removed} lines")
        compacted = compact_diff(staged_diff, max_lines=max_diff_lines)
        if compacted:
            parts.append("\n--- Staged diff ---")
            parts.append(compacted)
    elif unstaged_diff.strip():
        added, removed = count_diff_stats(unstaged_diff)
        parts.append(f"\nUnstaged changes: +{added} -{removed} lines")
        compacted = compact_diff(unstaged_diff, max_lines=max_diff_lines)
        if compacted:
            parts.append("\n--- Unstaged diff ---")
            parts.append(compacted)

    return "\n".join(parts)
