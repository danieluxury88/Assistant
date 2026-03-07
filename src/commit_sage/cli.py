"""CommitSage CLI — entry point for all commands."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from commit_sage import __version__

app = typer.Typer(
    name="commit-sage",
    help="AI-assisted Git commit message generator.",
    add_completion=False,
)

console = Console()
err_console = Console(stderr=True)


def _require_git_repo() -> Path:
    from commit_sage.git_tools import is_git_repo
    cwd = Path.cwd()
    if not is_git_repo(cwd):
        err_console.print("[bold red]Error:[/bold red] Not inside a Git repository.")
        raise typer.Exit(1)
    return cwd


def _load_summary(cwd: Path, staged_only: bool = False, unstaged_only: bool = False):
    from commit_sage.git_tools import (
        get_current_branch,
        get_staged_files,
        get_unstaged_files,
        get_staged_diff,
        get_unstaged_diff,
    )
    from commit_sage.config import get_app_config
    from commit_sage.summarizer import build_summary

    cfg = get_app_config()

    branch = get_current_branch(cwd)
    staged_files = get_staged_files(cwd) if not unstaged_only else []
    unstaged_files = get_unstaged_files(cwd) if not staged_only else []
    staged_diff = get_staged_diff(cwd) if not unstaged_only else ""
    unstaged_diff = get_unstaged_diff(cwd) if not staged_only else ""

    return build_summary(
        branch=branch,
        staged_files=staged_files,
        unstaged_files=unstaged_files,
        staged_diff=staged_diff,
        unstaged_diff=unstaged_diff,
        max_diff_lines=cfg.max_diff_lines,
    )


@app.command()
def analyze(
    staged_only: bool = typer.Option(False, "--staged-only", help="Show only staged changes."),
    unstaged_only: bool = typer.Option(False, "--unstaged-only", help="Show only unstaged changes."),
) -> None:
    """Analyze repository changes and display a summary."""
    from commit_sage.classifiers import classify_file, get_area, is_noisy

    cwd = _require_git_repo()
    summary = _load_summary(cwd, staged_only=staged_only, unstaged_only=unstaged_only)

    console.print(Panel(
        f"[bold]Branch:[/bold] [cyan]{summary.branch}[/cyan]",
        title="[bold blue]CommitSage Analysis[/bold blue]",
        box=box.ROUNDED,
    ))

    if summary.staged_files:
        table = Table(title="Staged Files", box=box.SIMPLE, show_header=True)
        table.add_column("Status", style="green", width=8)
        table.add_column("Category", style="yellow", width=12)
        table.add_column("File", style="white")
        for f in summary.staged_files:
            cat = classify_file(f)
            table.add_row("staged", cat, f)
        console.print(table)
    else:
        console.print("[dim]No staged files.[/dim]")

    if summary.unstaged_files:
        table = Table(title="Unstaged Files", box=box.SIMPLE, show_header=True)
        table.add_column("Status", style="yellow", width=8)
        table.add_column("Category", style="yellow", width=12)
        table.add_column("File", style="white")
        for f in summary.unstaged_files:
            cat = classify_file(f)
            table.add_row("modified", cat, f)
        console.print(table)
    else:
        console.print("[dim]No unstaged files.[/dim]")

    if summary.file_categories:
        cat_table = Table(title="File Breakdown", box=box.SIMPLE)
        cat_table.add_column("Category", style="cyan")
        cat_table.add_column("Count", justify="right")
        cat_table.add_column("Area", style="dim")
        for cat, count in sorted(summary.file_categories.items()):
            cat_table.add_row(cat, str(count), get_area(cat))
        console.print(cat_table)

    if summary.inferred_scope:
        console.print(f"\n[bold]Inferred scope:[/bold] [magenta]{summary.inferred_scope}[/magenta]")


@app.command()
def suggest(
    staged_only: bool = typer.Option(False, "--staged-only", help="Use only staged changes."),
    unstaged_only: bool = typer.Option(False, "--unstaged-only", help="Use only unstaged changes."),
    model: str = typer.Option(None, "--model", "-m", help="Override AI model name."),
) -> None:
    """Generate an AI commit message suggestion."""
    from commit_sage.commit_generator import generate_suggestion
    from commit_sage.llm_client import LLMError

    cwd = _require_git_repo()

    with console.status("[bold blue]Analyzing changes...[/bold blue]"):
        summary = _load_summary(cwd, staged_only=staged_only, unstaged_only=unstaged_only)

    all_files = list({*summary.staged_files, *summary.unstaged_files})
    if not all_files:
        console.print("[yellow]No changes detected. Nothing to suggest.[/yellow]")
        raise typer.Exit(0)

    with console.status("[bold blue]Asking AI for a commit suggestion...[/bold blue]"):
        try:
            suggestion = generate_suggestion(summary, model=model)
        except LLMError as e:
            err_console.print(f"[bold red]AI error:[/bold red] {e}")
            raise typer.Exit(1)

    _render_suggestion(suggestion)


@app.command()
def commit(
    staged_only: bool = typer.Option(False, "--staged-only", help="Use only staged changes."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt."),
    model: str = typer.Option(None, "--model", "-m", help="Override AI model name."),
) -> None:
    """Generate a commit suggestion and optionally create the commit."""
    from commit_sage.commit_generator import generate_suggestion
    from commit_sage.executor import confirm_and_commit
    from commit_sage.llm_client import LLMError

    cwd = _require_git_repo()

    with console.status("[bold blue]Analyzing changes...[/bold blue]"):
        summary = _load_summary(cwd, staged_only=staged_only)

    all_files = list({*summary.staged_files, *summary.unstaged_files})
    if not all_files:
        console.print("[yellow]No changes detected. Nothing to commit.[/yellow]")
        raise typer.Exit(0)

    if not summary.staged_files:
        console.print(
            "[yellow]Warning:[/yellow] No staged files detected. "
            "Stage files with [bold]git add[/bold] before committing."
        )
        raise typer.Exit(1)

    with console.status("[bold blue]Asking AI for a commit suggestion...[/bold blue]"):
        try:
            suggestion = generate_suggestion(summary, model=model)
        except LLMError as e:
            err_console.print(f"[bold red]AI error:[/bold red] {e}")
            raise typer.Exit(1)

    _render_suggestion(suggestion)
    confirm_and_commit(suggestion, cwd=cwd, auto_confirm=yes)


def _render_suggestion(suggestion) -> None:
    from rich.markdown import Markdown

    subject_line = suggestion.format_subject()

    console.print()
    console.print(Panel(
        f"[bold green]{subject_line}[/bold green]",
        title="[bold blue]Suggested Commit[/bold blue]",
        box=box.ROUNDED,
    ))

    if suggestion.body:
        console.print(Panel(
            suggestion.body,
            title="[dim]Body[/dim]",
            box=box.SIMPLE,
        ))

    if suggestion.confidence is not None:
        pct = int(suggestion.confidence * 100)
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        console.print(f"[dim]Confidence: {bar} {pct}%[/dim]")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit."),
) -> None:
    if version:
        console.print(f"CommitSage v{__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
