"""Manuscript dashboard: high-level overview of the full manuscript state."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def render_manuscript_dashboard(data: dict[str, Any]) -> None:
    """Render a manuscript overview dashboard."""
    manuscript = data.get("manuscript", {})
    stats = data.get("statistics", {})

    # Title panel
    console.print(Panel(
        f"[bold]{manuscript.get('title', 'Untitled')}[/bold]\n"
        f"Status: {manuscript.get('status', '?')} | "
        f"Words: {stats.get('total_words', 0):,} | "
        f"Chapters: {stats.get('total_chapters', 0)} | "
        f"Scenes: {stats.get('accepted_scenes', 0)}/{stats.get('total_scenes', 0)}",
        title="Manuscript Overview",
        border_style="cyan",
    ))

    # Chapter progress
    chapters = data.get("chapters", [])
    if chapters:
        ch_table = Table(title="Chapters", show_lines=False)
        ch_table.add_column("#", justify="right", style="dim")
        ch_table.add_column("Title")
        ch_table.add_column("Scenes", justify="right")
        ch_table.add_column("Words", justify="right")
        ch_table.add_column("Status")

        for ch in chapters:
            scenes = ch.get("scenes", [])
            accepted = sum(1 for s in scenes if s.get("status") == "accepted")
            words = sum(
                d.get("word_count", 0)
                for s in scenes
                for d in s.get("drafts", [])
                if d.get("branch_status") == "selected"
            )
            status = "[green]Complete[/green]" if accepted == len(scenes) else f"[yellow]{accepted}/{len(scenes)}[/yellow]"
            ch_table.add_row(
                str(ch.get("ordinal", "?")),
                ch.get("title", ""),
                str(len(scenes)),
                f"{words:,}",
                status,
            )
        console.print(ch_table)

    # Promise ledger
    promises = data.get("promises", [])
    if promises:
        p_table = Table(title="Promise Ledger", show_lines=False)
        p_table.add_column("Type", style="cyan")
        p_table.add_column("Description")
        p_table.add_column("Salience", justify="right")
        p_table.add_column("Status")

        for p in promises:
            status = p.get("status", "?")
            status_style = {
                "open": "yellow",
                "maturing": "blue",
                "resolved": "green",
                "overdue": "red",
                "abandoned": "dim",
            }.get(status, "white")
            p_table.add_row(
                p.get("type", "?"),
                p.get("description", "")[:60],
                f"{p.get('salience', 0):.1f}",
                f"[{status_style}]{status}[/{status_style}]",
            )
        console.print(p_table)

    # Token usage
    token_usage = data.get("token_usage", {})
    if token_usage:
        t_table = Table(title="Token Usage", show_lines=False)
        t_table.add_column("Tier", style="bold")
        t_table.add_column("Calls", justify="right")
        t_table.add_column("Tokens", justify="right")
        t_table.add_column("Remaining", justify="right")

        for tier, usage in token_usage.items():
            remaining = f"{usage['remaining']:,}" if usage.get("remaining") is not None else "unlimited"
            t_table.add_row(
                tier,
                str(usage.get("calls", 0)),
                f"{usage.get('total_tokens', 0):,}",
                remaining,
            )
        console.print(t_table)
