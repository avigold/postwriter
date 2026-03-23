"""Scene dashboard: displays draft, branches, scores, devices, and repair history."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def render_scene_dashboard(scene_data: dict[str, Any]) -> None:
    """Render a rich scene dashboard to the terminal."""
    # Header
    scene_id = scene_data.get("id", "?")[:8]
    purpose = scene_data.get("purpose", "")
    status = scene_data.get("status", "unknown")

    console.print(Panel(
        f"[bold]{purpose}[/bold]\nStatus: {status}",
        title=f"Scene {scene_id}",
        border_style="cyan",
    ))

    # Accepted draft preview
    accepted_prose = scene_data.get("accepted_prose", "")
    if accepted_prose:
        preview = accepted_prose[:500] + ("..." if len(accepted_prose) > 500 else "")
        console.print(Panel(preview, title="Accepted Draft", border_style="green"))

    # Branch comparison table
    branches = scene_data.get("branches", [])
    if branches:
        table = Table(title="Branches", show_lines=True)
        table.add_column("Label", style="cyan")
        table.add_column("Status")
        table.add_column("Words", justify="right")
        table.add_column("Composite", justify="right")
        table.add_column("Hard Pass")

        for b in branches:
            status_style = "green" if b.get("status") == "selected" else "dim"
            hard = "[green]PASS[/green]" if b.get("hard_pass") else "[red]FAIL[/red]"
            table.add_row(
                b.get("label", "?"),
                Text(b.get("status", "?"), style=status_style),
                str(b.get("word_count", 0)),
                f"{b.get('composite', 0):.3f}",
                hard,
            )
        console.print(table)

    # Score breakdown
    scores = scene_data.get("scores", {})
    if scores:
        score_table = Table(title="Score Breakdown", show_lines=False)
        score_table.add_column("Dimension", style="bold")
        score_table.add_column("Score", justify="right")
        score_table.add_column("Bar")

        for dim, val in sorted(scores.items()):
            if dim in ("hard_pass", "composite"):
                continue
            bar_len = int(val * 20)
            color = "green" if val >= 0.6 else "yellow" if val >= 0.4 else "red"
            bar = f"[{color}]{'█' * bar_len}{'░' * (20 - bar_len)}[/{color}]"
            score_table.add_row(dim.replace("_", " ").title(), f"{val:.2f}", bar)

        if "composite" in scores:
            score_table.add_row(
                "[bold]Composite[/bold]",
                f"[bold]{scores['composite']:.3f}[/bold]",
                "",
            )
        console.print(score_table)

    # Devices detected
    devices = scene_data.get("devices", [])
    if devices:
        dev_table = Table(title=f"Devices ({len(devices)})", show_lines=False)
        dev_table.add_column("Type", style="cyan")
        dev_table.add_column("Text")
        dev_table.add_column("Confidence", justify="right")

        for d in devices[:10]:
            dev_table.add_row(
                d.get("type", "?"),
                d.get("text", "")[:60],
                f"{d.get('confidence', 0):.1f}",
            )
        if len(devices) > 10:
            dev_table.add_row("...", f"+{len(devices) - 10} more", "")
        console.print(dev_table)

    # Repair history
    repairs = scene_data.get("repairs", [])
    if repairs:
        console.print(f"\n[bold]Repair History[/bold] ({len(repairs)} action(s))")
        for r in repairs:
            console.print(f"  [{r.get('priority', '?')}] {r.get('dimension', '?')}: {r.get('instruction', '')[:80]}")
