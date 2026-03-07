"""CommitSage CLI — entry point for all commands."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
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


def _load_summary(
    cwd: Path,
    staged_only: bool = False,
    unstaged_only: bool = False,
    include_files: set[str] | None = None,
):
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
        include_files=include_files,
    )


def _handle_mixed_changes(
    summary,
    cwd: Path,
    staged_only: bool = False,
    unstaged_only: bool = False,
):
    """
    When mixed/unrelated changes are detected, show the groups and ask
    the user how to proceed. Returns a rebuilt summary (possibly filtered),
    or raises typer.Exit if the user quits.

    Never unstages or discards anything without explicit user confirmation.
    """
    from commit_sage.git_tools import unstage_files, discard_file_changes, GitError

    areas = summary.mixed_areas
    if len(areas) <= 1:
        return summary

    # Display the mixed-changes warning
    console.print()
    console.print(Panel(
        "[bold yellow]Mixed changes detected[/bold yellow] — your staged changes span multiple unrelated areas.\n"
        "These may belong in separate commits.",
        box=box.ROUNDED,
        border_style="yellow",
    ))

    area_list = sorted(areas.items())
    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("#", style="bold cyan", width=3)
    table.add_column("Area", style="bold", width=12)
    table.add_column("Files", style="white")

    for i, (area, files) in enumerate(area_list, start=1):
        file_list = ", ".join(files[:4])
        if len(files) > 4:
            file_list += f" (+{len(files) - 4} more)"
        table.add_row(str(i), area, file_list)

    console.print(table)

    # Build the menu
    valid_nums = [str(i) for i in range(1, len(area_list) + 1)]
    console.print(
        "\n[dim]Options:[/dim]\n"
        "  [bold cyan]a[/bold cyan]   Proceed with all changes (one commit)\n"
        + "".join(
            f"  [bold cyan]{i}[/bold cyan]   Include only [bold]{area}[/bold] files\n"
            for i, (area, _) in enumerate(area_list, start=1)
        )
        + "  [bold cyan]d[/bold cyan]   Discard specific staged files (will confirm before any change)\n"
        "  [bold cyan]q[/bold cyan]   Quit"
    )

    choice = Prompt.ask("\nYour choice", default="a").strip().lower()

    if choice == "q":
        console.print("[dim]Aborted.[/dim]")
        raise typer.Exit(0)

    if choice == "a":
        return summary

    if choice == "d":
        return _handle_discard(summary, cwd)

    if choice in valid_nums:
        idx = int(choice) - 1
        selected_area, selected_files = area_list[idx]
        include = set(selected_files)

        console.print(
            f"\n[dim]Focusing on [bold]{selected_area}[/bold] "
            f"({len(selected_files)} file{'s' if len(selected_files) != 1 else ''}).[/dim]"
        )

        # Rebuild summary with only the selected files
        return _load_summary(cwd, staged_only=staged_only, unstaged_only=unstaged_only, include_files=include)

    # Unrecognised — treat as proceed with all
    console.print("[dim]Unrecognised choice — proceeding with all changes.[/dim]")
    return summary


def _handle_discard(summary, cwd: Path):
    """
    Interactive discard: show staged files, ask which to unstage/revert.
    Never touches the filesystem without explicit per-file confirmation.
    Returns a rebuilt summary after any changes.
    """
    from commit_sage.git_tools import unstage_files, discard_file_changes, GitError

    all_staged = summary.staged_files
    if not all_staged:
        console.print("[yellow]No staged files to discard.[/yellow]")
        return summary

    console.print("\n[bold]Staged files:[/bold]")
    for i, f in enumerate(all_staged, start=1):
        console.print(f"  [cyan]{i}[/cyan]  {f}")

    console.print(
        "\nEnter file numbers to [bold red]unstage[/bold red] (space-separated), or press Enter to cancel:"
    )
    raw = Prompt.ask("Files to unstage", default="").strip()

    if not raw:
        console.print("[dim]No changes made.[/dim]")
        return summary

    chosen_indices: list[int] = []
    for token in raw.split():
        try:
            idx = int(token) - 1
            if 0 <= idx < len(all_staged):
                chosen_indices.append(idx)
        except ValueError:
            pass

    if not chosen_indices:
        console.print("[dim]No valid selections. No changes made.[/dim]")
        return summary

    to_unstage = [all_staged[i] for i in chosen_indices]

    console.print("\nYou are about to [bold red]unstage[/bold red] these files:")
    for f in to_unstage:
        console.print(f"  [red]- {f}[/red]")

    confirmed = Confirm.ask("Confirm unstage?", default=False)
    if not confirmed:
        console.print("[dim]Cancelled. No changes made.[/dim]")
        return summary

    try:
        unstage_files(to_unstage, cwd=cwd)
        console.print(f"[green]Unstaged {len(to_unstage)} file(s).[/green]")
    except GitError as e:
        err_console.print(f"[bold red]Git error:[/bold red] {e}")
        raise typer.Exit(1)

    # Reload summary after unstaging
    return _load_summary(cwd)


@app.command()
def analyze(
    staged_only: bool = typer.Option(False, "--staged-only", help="Show only staged changes."),
    unstaged_only: bool = typer.Option(False, "--unstaged-only", help="Show only unstaged changes."),
) -> None:
    """Analyze repository changes and display a summary."""
    from commit_sage.classifiers import classify_file, get_area, is_mixed_changes

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

    if len(summary.mixed_areas) > 1:
        console.print(
            "\n[bold yellow]Note:[/bold yellow] Changes span multiple areas "
            f"({', '.join(summary.mixed_areas.keys())}). "
            "Consider splitting into separate commits."
        )


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

    # Handle mixed changes interactively
    if len(summary.mixed_areas) > 1:
        summary = _handle_mixed_changes(summary, cwd, staged_only=staged_only, unstaged_only=unstaged_only)

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

    # Handle mixed changes interactively
    if len(summary.mixed_areas) > 1:
        summary = _handle_mixed_changes(summary, cwd, staged_only=staged_only)

    # Re-check staged files after possible unstaging
    if not summary.staged_files:
        console.print("[yellow]No staged files remain. Nothing to commit.[/yellow]")
        raise typer.Exit(0)

    with console.status("[bold blue]Asking AI for a commit suggestion...[/bold blue]"):
        try:
            suggestion = generate_suggestion(summary, model=model)
        except LLMError as e:
            err_console.print(f"[bold red]AI error:[/bold red] {e}")
            raise typer.Exit(1)

    _render_suggestion(suggestion)
    confirm_and_commit(suggestion, cwd=cwd, auto_confirm=yes)


def _render_suggestion(suggestion) -> None:
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
