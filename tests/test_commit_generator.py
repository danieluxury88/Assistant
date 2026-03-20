import pytest
from unittest.mock import patch

from commit_sage.commit_generator import _parse_suggestion, generate_suggestion
from commit_sage.models import RepositoryChangeSummary


def _make_summary(**kwargs):
    defaults = dict(
        branch="main",
        staged_files=["src/main.py"],
        unstaged_files=[],
        file_categories={"python": 1},
        inferred_scope=None,
        summary_text="Branch: main\nChanged files (1):\n  [python] src/main.py",
    )
    defaults.update(kwargs)
    return RepositoryChangeSummary(**defaults)


def test_parse_suggestion_basic():
    data = {
        "commit_type": "feat",
        "scope": "auth",
        "subject": "add login endpoint",
        "body": None,
        "confidence": 0.9,
    }
    suggestion = _parse_suggestion(data, _make_summary())
    assert suggestion.commit_type == "feat"
    assert suggestion.scope == "auth"
    assert suggestion.subject == "add login endpoint"
    assert suggestion.confidence == pytest.approx(0.9)


def test_parse_suggestion_invalid_type_falls_back():
    data = {
        "commit_type": "invalidtype",
        "scope": None,
        "subject": "do something",
        "body": None,
        "confidence": 0.5,
    }
    suggestion = _parse_suggestion(data, _make_summary())
    assert suggestion.commit_type == "chore"


def test_parse_suggestion_strips_trailing_period():
    data = {
        "commit_type": "fix",
        "scope": None,
        "subject": "fix the bug.",
        "body": None,
        "confidence": None,
    }
    suggestion = _parse_suggestion(data, _make_summary())
    assert not suggestion.subject.endswith(".")


def test_format_subject_with_scope():
    data = {"commit_type": "feat", "scope": "api", "subject": "add endpoint", "body": None, "confidence": None}
    suggestion = _parse_suggestion(data, _make_summary())
    assert suggestion.format_subject() == "feat(api): add endpoint"


def test_format_subject_without_scope():
    data = {"commit_type": "docs", "scope": None, "subject": "update readme", "body": None, "confidence": None}
    suggestion = _parse_suggestion(data, _make_summary())
    assert suggestion.format_subject() == "docs: update readme"


def test_generate_suggestion_calls_api():
    summary = _make_summary()
    mock_response = '{"commit_type": "feat", "scope": "auth", "subject": "add login", "body": null, "confidence": 0.8}'
    with patch("commit_sage.commit_generator.call_llm", return_value=mock_response):
        suggestion = generate_suggestion(summary)
    assert suggestion.commit_type == "feat"
    assert suggestion.subject == "add login"
