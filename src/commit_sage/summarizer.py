"""Build compact, AI-ready summaries from Git change data."""

from commit_sage.classifiers import (
    categorize_files,
    group_files_by_area,
    infer_scope,
    is_mixed_changes,
    is_noisy,
    classify_file,
)
from commit_sage.diff_parser import compact_diff, count_diff_stats, filter_diff_by_files
from commit_sage.models import RepositoryChangeSummary


def build_summary(
    branch: str,
    staged_files: list[str],
    unstaged_files: list[str],
    staged_diff: str,
    unstaged_diff: str,
    max_diff_lines: int = 300,
    include_files: set[str] | None = None,
) -> RepositoryChangeSummary:
    """
    Build a RepositoryChangeSummary.

    If include_files is given, only those files (and their diffs) are
    included in the summary sent to the AI. The full staged/unstaged
    file lists are still stored on the model for the CLI to reference.
    """
    all_files = list({*staged_files, *unstaged_files})
    mixed_areas = group_files_by_area(all_files)

    # Determine which files feed into the AI summary
    effective_staged = staged_files
    effective_unstaged = unstaged_files
    effective_staged_diff = staged_diff
    effective_unstaged_diff = unstaged_diff

    if include_files is not None:
        effective_staged = [f for f in staged_files if f in include_files]
        effective_unstaged = [f for f in unstaged_files if f in include_files]
        effective_staged_diff = filter_diff_by_files(staged_diff, include_files)
        effective_unstaged_diff = filter_diff_by_files(unstaged_diff, include_files)

    effective_all = list({*effective_staged, *effective_unstaged})
    categories = categorize_files(effective_all)
    scope = infer_scope(effective_all)

    summary_text = _build_summary_text(
        branch=branch,
        staged_files=effective_staged,
        unstaged_files=effective_unstaged,
        staged_diff=effective_staged_diff,
        unstaged_diff=effective_unstaged_diff,
        max_diff_lines=max_diff_lines,
    )

    return RepositoryChangeSummary(
        branch=branch,
        staged_files=staged_files,
        unstaged_files=unstaged_files,
        file_categories=categories,
        inferred_scope=scope,
        summary_text=summary_text,
        mixed_areas=mixed_areas,
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
