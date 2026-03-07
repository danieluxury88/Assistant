import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitError(Exception):
    pass


def _run(args: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GitError(result.stderr.strip() or f"git command failed: {' '.join(args)}")
    return result.stdout


def is_git_repo(path: Path | None = None) -> bool:
    cwd = path or Path.cwd()
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def get_repo_root(path: Path | None = None) -> Path:
    cwd = path or Path.cwd()
    root = _run(["git", "rev-parse", "--show-toplevel"], cwd=cwd).strip()
    return Path(root)


def get_current_branch(cwd: Path | None = None) -> str:
    try:
        branch = _run(["git", "symbolic-ref", "--short", "HEAD"], cwd=cwd).strip()
        return branch
    except GitError:
        # Detached HEAD
        return _run(["git", "rev-parse", "--short", "HEAD"], cwd=cwd).strip()


@dataclass
class FileStatus:
    path: str
    staged: bool
    unstaged: bool
    status_code: str  # M, A, D, R, ?, etc.


def get_changed_files(cwd: Path | None = None) -> list[FileStatus]:
    output = _run(["git", "status", "--porcelain"], cwd=cwd)
    files: list[FileStatus] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        index_code = line[0]
        worktree_code = line[1]
        path = line[3:].strip()
        # Handle renames: "old -> new"
        if " -> " in path:
            path = path.split(" -> ")[-1]
        staged = index_code not in (" ", "?", "!")
        unstaged = worktree_code not in (" ", "?", "!")
        status_code = index_code if staged else worktree_code
        files.append(FileStatus(path=path, staged=staged, unstaged=unstaged, status_code=status_code))
    return files


def get_staged_files(cwd: Path | None = None) -> list[str]:
    return [f.path for f in get_changed_files(cwd) if f.staged]


def get_unstaged_files(cwd: Path | None = None) -> list[str]:
    return [f.path for f in get_changed_files(cwd) if f.unstaged]


def get_staged_diff(cwd: Path | None = None) -> str:
    try:
        return _run(["git", "diff", "--cached"], cwd=cwd)
    except GitError:
        return ""


def get_unstaged_diff(cwd: Path | None = None) -> str:
    try:
        return _run(["git", "diff"], cwd=cwd)
    except GitError:
        return ""


def has_staged_changes(cwd: Path | None = None) -> bool:
    return bool(get_staged_files(cwd))


def unstage_files(paths: list[str], cwd: Path | None = None) -> None:
    """Remove files from the staging area (git restore --staged)."""
    if not paths:
        return
    _run(["git", "restore", "--staged", *paths], cwd=cwd)


def discard_file_changes(paths: list[str], cwd: Path | None = None) -> None:
    """Discard unstaged working-tree changes for the given files (git restore)."""
    if not paths:
        return
    _run(["git", "restore", *paths], cwd=cwd)


def create_commit(message: str, cwd: Path | None = None) -> str:
    output = _run(["git", "commit", "-m", message], cwd=cwd)
    return output.strip()
