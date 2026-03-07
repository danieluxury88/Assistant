"""Build prompts for AI commit suggestion generation."""

from commit_sage.models import RepositoryChangeSummary


SYSTEM_PROMPT = """\
You are CommitSage, an expert at writing concise, high-quality Git commit messages.
You follow the Conventional Commits specification strictly.
You respond ONLY with valid JSON — no explanation, no markdown, no code fences.
"""

COMMIT_MESSAGE_TEMPLATE = """\
Analyze the following Git changes and generate a commit message.

{summary}

Respond with JSON in exactly this format:
{{
  "commit_type": "<type>",
  "scope": "<scope or null>",
  "subject": "<concise imperative subject, max 72 chars>",
  "body": "<optional multi-line body or null>",
  "confidence": <float 0.0-1.0>
}}

Valid commit types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert

Rules:
- subject must be imperative mood (e.g. "add", "fix", "update")
- subject must NOT end with a period
- scope is a short noun (e.g. "auth", "dashboard", "api") or null
- body should explain WHY, not WHAT (null if not needed)
- confidence reflects how certain you are about the type/subject
"""


def build_prompt(summary: RepositoryChangeSummary) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) tuple for the AI call.
    """
    user_prompt = COMMIT_MESSAGE_TEMPLATE.format(summary=summary.summary_text)
    return SYSTEM_PROMPT, user_prompt
