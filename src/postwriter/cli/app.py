"""Main CLI entry point for postwriter."""

from __future__ import annotations

import asyncio
from pathlib import Path

import click

from postwriter.cli import display
from postwriter.config import get_settings
from postwriter.context.loader import ContextLoader


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Postwriter: Orchestrated Long-Form Fiction Generation."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(new)


@cli.command()
@click.option("--context-dir", type=click.Path(exists=False), default=None,
              help="Path to context files directory. Defaults to ./context/")
@click.option("--project-dir", type=click.Path(exists=True), default=".",
              help="Project root directory.")
@click.option("--profile", type=click.Choice(["fast_draft", "high_quality", "budget_conscious"]),
              default=None, help="Generation profile.")
def new(context_dir: str | None, project_dir: str = ".", profile: str | None = None) -> None:
    """Start a new novel project with interactive bootstrap."""
    asyncio.run(_run_new(context_dir, project_dir, profile))


@cli.command()
@click.argument("manuscript_id")
@click.option("--format", "fmt", type=click.Choice(["markdown", "json", "report", "all"]),
              default="markdown", help="Export format.")
@click.option("--output-dir", type=click.Path(), default="./output",
              help="Output directory.")
def export(manuscript_id: str, fmt: str, output_dir: str) -> None:
    """Export a manuscript."""
    asyncio.run(_run_export(manuscript_id, fmt, Path(output_dir)))


@cli.command()
@click.argument("manuscript_id")
def dashboard(manuscript_id: str) -> None:
    """Show manuscript dashboard."""
    asyncio.run(_run_dashboard(manuscript_id))


@cli.command()
def profiles() -> None:
    """List available generation profiles."""
    from postwriter.profiles import list_profiles
    display.section("Available Profiles")
    for p in list_profiles():
        display.info(f"  {p['name']}: {p['description']}")


# ------------------------------------------------------------------
# Async implementations
# ------------------------------------------------------------------

async def _run_new(context_dir: str | None, project_dir: str, profile_name: str | None) -> None:
    from postwriter.cli.bootstrap import run_bootstrap
    from postwriter.db.session import get_engine, get_session_factory
    from postwriter.llm.client import LLMClient
    from postwriter.orchestrator.planner import PlanningOrchestrator

    settings = get_settings()

    # Apply profile if specified
    if profile_name:
        from postwriter.profiles import apply_profile
        apply_profile(profile_name, settings.orchestrator, settings.llm)
        display.info(f"Using profile: {profile_name}")

    display.banner()
    display.info(f"Project directory: {Path(project_dir).resolve()}")

    # Load context files
    ctx_path = Path(context_dir) if context_dir else Path(project_dir) / "context"
    context_loader = ContextLoader(ctx_path)
    context_files = context_loader.load()
    display.show_context_summary(context_loader.summary())

    # Interactive bootstrap
    creative_brief = run_bootstrap(context_files)

    # Confirm
    display.section("Ready to Plan")
    display.info(f"Genre: {creative_brief.get('genre', 'unspecified')}")
    display.info(f"Target: ~{creative_brief.get('target_word_count', 80000)} words")
    if not display.confirm("Begin planning?"):
        display.warning("Aborted.")
        return

    if not settings.llm.anthropic_api_key:
        display.error("No Anthropic API key found. Set PW_LLM_ANTHROPIC_API_KEY or add it to .env")
        return

    engine = get_engine(settings)
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        llm = LLMClient(settings.llm)
        try:
            # Phase 1: Planning
            planner = PlanningOrchestrator(session, llm)
            manuscript = await planner.run(creative_brief, context_files)
            display.success(f"\nManuscript ID: {manuscript.id}")

            # Phase 2: Drafting
            if display.confirm("Proceed to drafting?"):
                from postwriter.orchestrator.engine import FictionOrchestrator
                drafter = FictionOrchestrator(
                    session, llm, settings=settings.orchestrator,
                    context_files=context_files,
                )
                await drafter.run(manuscript.id)

                # Phase 3: Global Revision
                if display.confirm("Run global revision passes?"):
                    from postwriter.orchestrator.global_revision import GlobalRevisionOrchestrator
                    reviser = GlobalRevisionOrchestrator(session, llm)
                    await reviser.run(manuscript.id)

                # Phase 4: Export
                if display.confirm("Export manuscript?"):
                    from postwriter.export.markdown import export_markdown
                    from postwriter.export.report import export_report
                    output_dir = Path(project_dir) / "output"

                    md_path = output_dir / "manuscript.md"
                    text = await export_markdown(session, manuscript.id, md_path)
                    display.success(f"Manuscript exported: {md_path} ({len(text):,} chars)")

                    report_path = output_dir / "report.md"
                    await export_report(session, manuscript.id, llm.budget, report_path)
                    display.success(f"Report exported: {report_path}")

        finally:
            await llm.close()

    await engine.dispose()


async def _run_export(manuscript_id: str, fmt: str, output_dir: Path) -> None:
    import uuid

    from postwriter.db.session import get_engine, get_session_factory
    from postwriter.export.json_export import export_json
    from postwriter.export.markdown import export_markdown
    from postwriter.export.report import export_report

    settings = get_settings()
    engine = get_engine(settings)
    session_factory = get_session_factory(engine)
    mid = uuid.UUID(manuscript_id)

    async with session_factory() as session:
        if fmt in ("markdown", "all"):
            path = output_dir / "manuscript.md"
            text = await export_markdown(session, mid, path)
            display.success(f"Markdown exported: {path} ({len(text):,} chars)")

        if fmt in ("json", "all"):
            path = output_dir / "manuscript.json"
            data = await export_json(session, mid, path)
            display.success(f"JSON exported: {path}")

        if fmt in ("report", "all"):
            path = output_dir / "report.md"
            report = await export_report(session, mid, output_path=path)
            stats = report.get("statistics", {})
            display.success(f"Report exported: {path} ({stats.get('total_words', 0):,} words)")

    await engine.dispose()


async def _run_dashboard(manuscript_id: str) -> None:
    import uuid

    from postwriter.cli.dashboards.manuscript import render_manuscript_dashboard
    from postwriter.db.session import get_engine, get_session_factory
    from postwriter.export.json_export import export_json

    settings = get_settings()
    engine = get_engine(settings)
    session_factory = get_session_factory(engine)
    mid = uuid.UUID(manuscript_id)

    async with session_factory() as session:
        data = await export_json(session, mid)
        if not data:
            display.error("Manuscript not found.")
            return
        render_manuscript_dashboard(data)

    await engine.dispose()


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
