import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from commit_sage.git_tools import (
    is_git_repo,
    get_current_branch,
    get_changed_files,
    get_staged_files,
    get_unstaged_files,
    FileStatus,
)


def test_is_git_repo_true(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    assert is_git_repo(tmp_path) is True


def test_is_git_repo_false(tmp_path):
    assert is_git_repo(tmp_path) is False


def test_get_current_branch(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "checkout", "-b", "main"], cwd=tmp_path, capture_output=True)
    branch = get_current_branch(tmp_path)
    assert branch == "main"


def test_get_changed_files_empty(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    files = get_changed_files(tmp_path)
    assert files == []


def test_get_changed_files_new_file(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "test.py").write_text("print('hello')")
    files = get_changed_files(tmp_path)
    assert any(f.path == "test.py" for f in files)


def test_staged_files_after_add(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)
    (tmp_path / "test.py").write_text("x = 1")
    subprocess.run(["git", "add", "test.py"], cwd=tmp_path, check=True, capture_output=True)
    staged = get_staged_files(tmp_path)
    assert "test.py" in staged
