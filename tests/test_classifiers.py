import pytest
from commit_sage.classifiers import (
    classify_file,
    get_area,
    is_noisy,
    categorize_files,
    infer_scope,
)


def test_classify_python():
    assert classify_file("src/app/main.py") == "python"


def test_classify_js():
    assert classify_file("assets/app.js") == "js"


def test_classify_ts():
    assert classify_file("src/index.ts") == "ts"


def test_classify_css():
    assert classify_file("styles/main.scss") == "css"


def test_classify_markdown():
    assert classify_file("README.md") == "docs"


def test_classify_yaml():
    assert classify_file(".github/workflows/ci.yml") == "yaml"


def test_classify_unknown():
    assert classify_file("some_file.xyz") == "unknown"


def test_is_noisy_lockfile():
    assert is_noisy("package-lock.json") is True
    assert is_noisy("yarn.lock") is True
    assert is_noisy("composer.lock") is True


def test_is_noisy_minified():
    assert is_noisy("dist/bundle.min.js") is True


def test_is_noisy_normal_file():
    assert is_noisy("src/main.py") is False


def test_categorize_files():
    files = ["src/main.py", "src/utils.py", "README.md", "package-lock.json"]
    cats = categorize_files(files)
    assert cats.get("python") == 2
    assert cats.get("docs") == 1
    assert "lock" not in cats  # noise is excluded


def test_infer_scope_single_area():
    files = ["src/auth/login.py", "src/auth/logout.py"]
    scope = infer_scope(files)
    assert scope is not None


def test_infer_scope_mixed():
    files = ["src/main.py", "styles/app.css", "README.md"]
    scope = infer_scope(files)
    # Mixed areas should return None
    assert scope is None
