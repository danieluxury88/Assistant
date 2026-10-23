"""Transform AI output into structured CommitSuggestion objects."""

from commit_sage.llm_client import call_llm, parse_json_response, LLMError
from commit_sage.models import CommitSuggestion, RepositoryChangeSummary
from commit_sage.prompt_builder import build_prompt

VALID_TYPES = {
    "feat", "fix", "docs", "style", "refactor",
    "perf", "test", "build", "ci", "chore", "revert",
}


def generate_suggestion(
    summary: RepositoryChangeSummary,
    model: str | None = None,
    profile: str | None = None,
) -> CommitSuggestion:
    """
    Call the AI provider with the change summary and return a CommitSuggestion.
    Raises LLMError if the API call fails.
    """
    system_prompt, user_prompt = build_prompt(summary)
    raw_response = call_llm(system_prompt, user_prompt, model=model, profile=profile)
    data = parse_json_response(raw_response)
    return _parse_suggestion(data, summary)


def _parse_suggestion(data: dict, summary: RepositoryChangeSummary) -> CommitSuggestion:
    commit_type = str(data.get("commit_type", "chore")).lower().strip()
    if commit_type not in VALID_TYPES:
        commit_type = "chore"

    scope = data.get("scope") or summary.inferred_scope
    if scope:
        scope = str(scope).lower().strip()[:30]

    subject = str(data.get("subject", "update files")).strip()
    # Ensure no trailing period
    subject = subject.rstrip(".")
    # Capitalize first letter
    if subject:
        subject = subject[0].lower() + subject[1:]

    body = data.get("body")
    if body:
        body = str(body).strip() or None

    confidence_raw = data.get("confidence")
    confidence: float | None = None
    if confidence_raw is not None:
        try:
            confidence = float(confidence_raw)
            confidence = max(0.0, min(1.0, confidence))
        except (TypeError, ValueError):
            confidence = None

    return CommitSuggestion(
        commit_type=commit_type,
        scope=scope,
        subject=subject,
        body=body,
        confidence=confidence,
    )
