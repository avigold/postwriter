"""Interactive bootstrap questionnaire for creating a new novel project."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.prompt import Prompt

from postwriter.cli.display import info, section, show_context_summary
from postwriter.context.loader import ContextFile, ContextType

console = Console()


def run_bootstrap(context_files: list[ContextFile] | None = None) -> dict[str, Any]:
    """Run the interactive bootstrap questionnaire.

    Returns a creative brief dict with all user inputs. If context files
    are provided, pre-fills answers where possible and skips redundant questions.
    """
    context_files = context_files or []

    # Check what the context files already provide
    prefilled = _extract_prefilled(context_files)

    section("Novel Setup")
    info("Answer the following questions to shape your novel. Press Enter to skip optional ones.\n")

    brief: dict[str, Any] = {}

    # Genre
    if prefilled.get("genre"):
        brief["genre"] = prefilled["genre"]
        info(f"Genre (from context): {brief['genre']}")
    else:
        brief["genre"] = Prompt.ask(
            "  [bold]Genre[/bold]",
            default="literary fiction",
        )

    # Setting
    brief["setting"] = Prompt.ask(
        "  [bold]Setting[/bold] (place and atmosphere)",
        default=prefilled.get("setting", ""),
    )

    # Time period
    brief["time_period"] = Prompt.ask(
        "  [bold]Time period[/bold]",
        default=prefilled.get("time_period", "present day"),
    )

    # Tone
    brief["tone"] = Prompt.ask(
        "  [bold]Tone[/bold] (e.g., atmospheric, tense, darkly comic, elegiac)",
        default=prefilled.get("tone", ""),
    )

    section("Story")

    # Protagonist
    brief["protagonist"] = Prompt.ask(
        "  [bold]Protagonist[/bold] (who is the main character?)",
        default=prefilled.get("protagonist", ""),
    )

    # Central conflict
    brief["central_conflict"] = Prompt.ask(
        "  [bold]Central conflict[/bold] (what is the core tension?)",
        default=prefilled.get("central_conflict", ""),
    )

    # Ending direction
    brief["ending_direction"] = Prompt.ask(
        "  [bold]Ending direction[/bold] (how should the novel resolve — or not?)",
        default=prefilled.get("ending_direction", ""),
    )

    section("Themes & Style")

    # Themes
    themes_input = Prompt.ask(
        "  [bold]Themes[/bold] (comma-separated, or Enter to let the system decide)",
        default=", ".join(prefilled.get("themes", [])) if prefilled.get("themes") else "",
    )
    brief["themes"] = [t.strip() for t in themes_input.split(",") if t.strip()] if themes_input else []

    # Voice preferences
    brief["voice_preferences"] = Prompt.ask(
        "  [bold]Voice preferences[/bold] (e.g., sparse, lyrical, ironic, intimate)",
        default=prefilled.get("voice_preferences", ""),
    )

    # Constraints
    constraints_input = Prompt.ask(
        "  [bold]Constraints[/bold] (comma-separated, e.g., single POV, no supernatural)",
        default="",
    )
    brief["constraints"] = [c.strip() for c in constraints_input.split(",") if c.strip()] if constraints_input else []

    section("Scope")

    brief["target_word_count"] = int(
        Prompt.ask("  [bold]Target word count[/bold]", default="80000")
    )
    brief["target_chapters"] = Prompt.ask(
        "  [bold]Target chapter range[/bold]", default="30-40"
    )

    return brief


def _extract_prefilled(context_files: list[ContextFile]) -> dict[str, Any]:
    """Extract any pre-fillable fields from loaded context files.

    This does simple keyword extraction from context file content.
    It doesn't try to be comprehensive — just catches obvious cases.
    """
    prefilled: dict[str, Any] = {}

    for cf in context_files:
        if cf.is_image:
            continue

        content_lower = cf.content.lower()
        fm = cf.frontmatter

        # Check frontmatter for explicit fields
        for key in ("genre", "setting", "time_period", "tone", "protagonist"):
            if key in fm and fm[key]:
                prefilled[key] = fm[key]

        # Extract themes from frontmatter
        if "themes" in fm:
            themes_raw = fm["themes"]
            if isinstance(themes_raw, str):
                prefilled["themes"] = [t.strip() for t in themes_raw.split(",")]

    return prefilled
