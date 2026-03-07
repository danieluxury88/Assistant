"""Handle user confirmation and git commit execution."""

from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm

from commit_sage.git_tools import create_commit, GitError
from commit_sage.models import CommitSuggestion

console = Console()


def confirm_and_commit(
    suggestion: CommitSuggestion,
    cwd: Path | None = None,
    auto_confirm: bool = False,
    include_files: list[str] | None = None,
) -> bool:
    """
    Show the final suggestion, ask for confirmation, and create the commit.
    Returns True if commit was created, False otherwise.
    """
    full_message = suggestion.format_full()

    console.print()
    console.rule("[bold green]Final commit message[/bold green]")
    console.print(f"\n[bold cyan]{full_message}[/bold cyan]\n")

    if not auto_confirm:
        confirmed = Confirm.ask("Create this commit?", default=True)
        if not confirmed:
            console.print("[yellow]Commit cancelled.[/yellow]")
            return False

    try:
        output = create_commit(full_message, cwd=cwd, paths=include_files)
        console.print(f"[bold green]Committed:[/bold green] {suggestion.format_subject()}")
        if output:
            console.print(f"[dim]{output}[/dim]")
        return True
    except GitError as e:
        console.print(f"[bold red]Git error:[/bold red] {e}")
        raise typer.Exit(1)
