from pydantic import BaseModel, Field


class RepositoryChangeSummary(BaseModel):
    branch: str
    staged_files: list[str]
    unstaged_files: list[str]
    file_categories: dict[str, int]
    inferred_scope: str | None = None
    summary_text: str
    mixed_areas: dict[str, list[str]] = Field(default_factory=dict)


class CommitSuggestion(BaseModel):
    commit_type: str
    scope: str | None = None
    subject: str
    body: str | None = None
    confidence: float | None = None

    def format_subject(self) -> str:
        if self.scope:
            return f"{self.commit_type}({self.scope}): {self.subject}"
        return f"{self.commit_type}: {self.subject}"

    def format_full(self) -> str:
        msg = self.format_subject()
        if self.body:
            msg = f"{msg}\n\n{self.body}"
        return msg


class AppConfig(BaseModel):
    ai_provider: str = "anthropic"
    api_model: str = "claude-haiku-4-5-20251001"
    local_endpoint: str | None = None
    commit_style: str = "conventional"
    ignored_patterns: list[str] = Field(default_factory=list)
    max_diff_lines: int = 300
