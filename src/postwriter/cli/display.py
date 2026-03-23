"""Rich-based display utilities for the CLI."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def banner() -> None:
    console.print(
        Panel(
            Text("POSTWRITER", style="bold cyan", justify="center"),
            subtitle="Orchestrated Long-Form Fiction",
            border_style="cyan",
        )
    )


def section(title: str) -> None:
    console.print(f"\n[bold cyan]{title}[/bold cyan]")
    console.print("[dim]" + "─" * 60 + "[/dim]")


def info(msg: str) -> None:
    console.print(f"[dim]  {msg}[/dim]")


def success(msg: str) -> None:
    console.print(f"[green]  {msg}[/green]")


def warning(msg: str) -> None:
    console.print(f"[yellow]  {msg}[/yellow]")


def error(msg: str) -> None:
    console.print(f"[red]  {msg}[/red]")


def show_premise(premise: str, controlling_design: dict[str, Any]) -> None:
    section("Generated Premise")
    console.print(Markdown(premise))
    console.print()

    section("Controlling Design")
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold")
    table.add_column("Value")
    for key, value in controlling_design.items():
        if isinstance(value, list):
            value = "\n".join(f"- {v}" for v in value)
        table.add_row(key.replace("_", " ").title(), str(value))
    console.print(table)


def show_act_structure(acts: list[dict[str, Any]]) -> None:
    section("Act Structure")
    for act in acts:
        console.print(
            f"\n  [bold]Act {act.get('ordinal', '?')}: {act.get('name', 'Unnamed')}[/bold]"
        )
        console.print(f"  Purpose: {act.get('purpose', '')}")
        if act.get("chapter_count"):
            console.print(f"  Chapters: ~{act['chapter_count']}")


def show_characters(characters: list[dict[str, Any]]) -> None:
    section("Cast")
    for char in characters:
        pov = " [cyan](POV)[/cyan]" if char.get("is_pov_character") else ""
        console.print(f"\n  [bold]{char.get('name', 'Unknown')}{pov}[/bold]")
        if char.get("biography"):
            console.print(f"  {char['biography'][:200]}")
        if char.get("arc_hypothesis"):
            console.print(f"  [dim]Arc: {char['arc_hypothesis']}[/dim]")


def show_context_summary(summary: str) -> None:
    if summary and "No context files" not in summary:
        section("Context Files")
        console.print(f"  {summary}")


def show_progress(phase: str, current: int, total: int, detail: str = "") -> None:
    pct = (current / total * 100) if total > 0 else 0
    bar_width = 30
    filled = int(bar_width * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_width - filled)
    detail_str = f" — {detail}" if detail else ""
    console.print(
        f"\r  [cyan]{phase}[/cyan] [{bar}] {current}/{total} ({pct:.0f}%){detail_str}",
        end="",
    )


def confirm(prompt: str, default: bool = True) -> bool:
    """Ask a yes/no question."""
    suffix = " [Y/n] " if default else " [y/N] "
    response = console.input(f"\n  [bold]{prompt}[/bold]{suffix}").strip().lower()
    if not response:
        return default
    return response in ("y", "yes")
