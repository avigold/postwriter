"""Main CLI entry point for postwriter.

Running `postwriter` in any directory will:
1. Detect if a project exists (.postwriter file)
2. If not, start a new project (bootstrap -> plan -> draft -> revise -> export)
3. If interrupted, offer to resume from where it left off
4. If complete, offer to export or start fresh
"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

import click
from rich.prompt import Prompt

from postwriter.cli import display
from postwriter.config import get_settings
from postwriter.context.loader import ContextLoader
from postwriter.project import ProjectState, detect_project, save_project, update_phase


@click.command()
@click.option("--profile", type=click.Choice(["fast_draft", "high_quality", "budget_conscious"]),
              default=None, help="Generation profile. If omitted, you'll be asked.")
@click.option("--project-dir", type=click.Path(exists=True), default=".",
              help="Project root directory.", show_default=True)
@click.option("--context-dir", type=click.Path(exists=False), default=None,
              help="Path to context files. Defaults to ./context/")
def cli(profile: str | None, project_dir: str = ".", context_dir: str | None = None) -> None:
    """Postwriter: Orchestrated Long-Form Fiction Generation."""
    asyncio.run(_run(Path(project_dir), profile, context_dir))


async def _run(project_dir: Path, profile_name: str | None, context_dir: str | None) -> None:
    from postwriter.logging_config import setup_logging

    project_dir = project_dir.resolve()
    log_file = setup_logging(log_dir=project_dir / "logs")

    display.banner()
    display.info(f"Project: {project_dir}")
    display.info(f"Logging to: {log_file}")

    # Check for existing project
    state = detect_project(project_dir)

    if state:
        await _handle_existing(project_dir, state, context_dir)
    else:
        await _handle_new(project_dir, profile_name, context_dir)


async def _handle_existing(
    project_dir: Path, state: ProjectState, context_dir: str | None
) -> None:
    """Handle an existing project -- resume or export."""
    display.section("Existing Project Detected")
    display.info(f"Title: {state.title or 'Untitled'}")
    display.info(f"Phase: {state.phase}")
    display.info(f"Manuscript: {state.manuscript_id[:8]}...")

    if state.phase == "complete":
        choice = Prompt.ask(
            "  [bold]Manuscript is complete. What would you like to do?[/bold]",
            choices=["export", "dashboard", "new"],
            default="export",
        )
        if choice == "export":
            await _do_export(project_dir, uuid.UUID(state.manuscript_id))
        elif choice == "dashboard":
            await _do_dashboard(uuid.UUID(state.manuscript_id))
        elif choice == "new":
            if display.confirm("Start a completely new novel? (Current project data remains in the database)"):
                await _handle_new(project_dir, None, context_dir)
        return

    # Interrupted project
    if not display.confirm(f"Resume {state.phase}?"):
        choice = Prompt.ask(
            "  [bold]What would you like to do?[/bold]",
            choices=["resume", "export_partial", "new"],
            default="resume",
        )
        if choice == "new":
            await _handle_new(project_dir, state.profile, context_dir)
            return
        elif choice == "export_partial":
            await _do_export(project_dir, uuid.UUID(state.manuscript_id))
            return

    # Resume
    await _resume(project_dir, state, context_dir)


async def _handle_new(
    project_dir: Path, profile_name: str | None, context_dir: str | None
) -> None:
    """Start a new project from scratch."""
    from postwriter.cli.bootstrap import run_bootstrap

    settings = get_settings()

    # Ask for profile if not specified
    if not profile_name:
        display.section("Generation Profile")
        display.info("  fast_draft:       Fewer branches, faster, cheaper")
        display.info("  high_quality:     More branches, more repair rounds")
        display.info("  budget_conscious: Minimise API costs")
        profile_name = Prompt.ask(
            "\n  [bold]Choose a profile[/bold]",
            choices=["fast_draft", "high_quality", "budget_conscious"],
            default="fast_draft",
        )

    from postwriter.profiles import apply_profile
    apply_profile(profile_name, settings.orchestrator, settings.llm)
    display.success(f"Profile: {profile_name}")

    # Load context files
    ctx_path = Path(context_dir) if context_dir else project_dir / "context"
    context_loader = ContextLoader(ctx_path)
    context_files = context_loader.load()
    display.show_context_summary(context_loader.summary())

    # Interactive bootstrap
    creative_brief = run_bootstrap(context_files)

    # Confirm
    display.section("Ready to Plan")
    display.info(f"Genre: {creative_brief.get('genre', 'unspecified')}")
    display.info(f"Target: ~{creative_brief.get('target_word_count', 80000)} words")
    if not display.confirm("Begin?"):
        display.warning("Aborted.")
        return

    if not settings.llm.anthropic_api_key:
        display.error("No Anthropic API key found. Set PW_LLM_ANTHROPIC_API_KEY or add it to .env")
        return

    # Run the full pipeline
    from postwriter.db.session import get_engine, get_session_factory
    from postwriter.llm.client import LLMClient
    from postwriter.orchestrator.planner import PlanningOrchestrator

    engine = get_engine(settings)
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        llm = LLMClient(settings.llm)
        try:
            # Phase 1: Planning
            planner = PlanningOrchestrator(session, llm)
            manuscript = await planner.run(
                creative_brief, context_files,
                project_dir=str(project_dir), profile_name=profile_name,
            )

            # Save project state (also saved early inside planner.run,
            # but update here in case title changed during planning)
            state = ProjectState(
                manuscript_id=str(manuscript.id),
                phase="drafting",
                profile=profile_name,
                title=manuscript.title,
            )
            save_project(project_dir, state)
            display.success(f"Manuscript ID: {manuscript.id}")

            # Phase 2: Drafting
            await _do_drafting(session, llm, manuscript.id, settings, context_files, project_dir)

            # Phase 3: Revision
            update_phase(project_dir, "revising")
            await _do_revision(session, llm, manuscript.id, project_dir)

            # Phase 4: Export
            update_phase(project_dir, "complete")
            await _do_export(project_dir, manuscript.id)

        finally:
            await llm.close()

    await engine.dispose()


async def _resume(
    project_dir: Path, state: ProjectState, context_dir: str | None
) -> None:
    """Resume an interrupted project."""
    settings = get_settings()

    if state.profile:
        from postwriter.profiles import apply_profile
        apply_profile(state.profile, settings.orchestrator, settings.llm)

    if not settings.llm.anthropic_api_key:
        display.error("No Anthropic API key found. Set PW_LLM_ANTHROPIC_API_KEY or add it to .env")
        return

    # Load context files
    ctx_path = Path(context_dir) if context_dir else project_dir / "context"
    context_loader = ContextLoader(ctx_path)
    context_files = context_loader.load()

    from postwriter.db.session import get_engine, get_session_factory
    from postwriter.llm.client import LLMClient

    engine = get_engine(settings)
    session_factory = get_session_factory(engine)
    manuscript_id = uuid.UUID(state.manuscript_id)

    async with session_factory() as session:
        llm = LLMClient(settings.llm)
        try:
            if state.phase == "planning":
                # Planning was interrupted — check what exists and decide
                from postwriter.canon.store import CanonStore
                store = CanonStore(session)
                chapters = await store.get_all_chapters(manuscript_id)
                scenes_exist = False
                for ch in chapters:
                    scenes = await store.get_scenes(ch.id)
                    if scenes:
                        scenes_exist = True
                        break

                if scenes_exist:
                    # Planning completed enough to have scenes — go to drafting
                    display.section("Resuming from Drafting")
                    display.info("Planning appears complete. Proceeding to drafting...")
                    update_phase(project_dir, "drafting")
                    await _do_drafting(session, llm, manuscript_id, settings, context_files, project_dir)
                elif chapters:
                    # Have chapters but no scenes — need to re-run scene planning
                    display.section("Resuming Planning")
                    display.info(f"Found {len(chapters)} chapters. Scene planning may be incomplete.")
                    display.warning("Cannot resume partial planning yet. Please start a new project.")
                    return
                else:
                    # Very early interruption — need to re-plan
                    display.section("Resuming Planning")
                    display.info("Planning was interrupted early. Re-running from premise...")
                    display.warning("Cannot resume partial planning yet. Please start a new project.")
                    return

                update_phase(project_dir, "revising")
                await _do_revision(session, llm, manuscript_id, project_dir)

                update_phase(project_dir, "complete")
                await _do_export(project_dir, manuscript_id)

            elif state.phase == "drafting":
                display.section("Resuming Drafting")
                display.info("Skipping already-accepted scenes...")
                await _do_drafting(session, llm, manuscript_id, settings, context_files, project_dir)

                update_phase(project_dir, "revising")
                await _do_revision(session, llm, manuscript_id, project_dir)

                update_phase(project_dir, "complete")
                await _do_export(project_dir, manuscript_id)

            elif state.phase == "revising":
                display.section("Resuming Revision")
                await _do_revision(session, llm, manuscript_id, project_dir)

                update_phase(project_dir, "complete")
                await _do_export(project_dir, manuscript_id)

        finally:
            await llm.close()

    await engine.dispose()


async def _do_drafting(session, llm, manuscript_id, settings, context_files, project_dir):
    """Run the drafting phase."""
    from postwriter.orchestrator.engine import FictionOrchestrator

    update_phase(project_dir, "drafting")
    drafter = FictionOrchestrator(
        session, llm, settings=settings.orchestrator,
        context_files=context_files,
    )
    await drafter.run(manuscript_id)


async def _do_revision(session, llm, manuscript_id, project_dir):
    """Run global revision."""
    from postwriter.orchestrator.global_revision import GlobalRevisionOrchestrator

    display.section("Global Revision")
    if display.confirm("Run global revision passes?"):
        reviser = GlobalRevisionOrchestrator(session, llm)
        await reviser.run(manuscript_id)


async def _do_export(project_dir: Path, manuscript_id: uuid.UUID) -> None:
    """Export the manuscript."""
    from postwriter.db.session import get_engine, get_session_factory
    from postwriter.export.markdown import export_markdown
    from postwriter.export.report import export_report

    settings = get_settings()
    engine = get_engine(settings)
    session_factory = get_session_factory(engine)
    output_dir = project_dir / "output"

    display.section("Export")

    async with session_factory() as session:
        md_path = output_dir / "manuscript.md"
        text = await export_markdown(session, manuscript_id, md_path)
        if text:
            display.success(f"Manuscript: {md_path} ({len(text):,} chars)")

        report_path = output_dir / "report.md"
        report = await export_report(session, manuscript_id, output_path=report_path)
        if report:
            words = report.get("statistics", {}).get("total_words", 0)
            display.success(f"Report: {report_path} ({words:,} words)")

    await engine.dispose()


async def _do_dashboard(manuscript_id: uuid.UUID) -> None:
    """Show the manuscript dashboard."""
    from postwriter.cli.dashboards.manuscript import render_manuscript_dashboard
    from postwriter.db.session import get_engine, get_session_factory
    from postwriter.export.json_export import export_json

    settings = get_settings()
    engine = get_engine(settings)
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        data = await export_json(session, manuscript_id)
        if not data:
            display.error("Manuscript not found.")
            return
        render_manuscript_dashboard(data)

    await engine.dispose()


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
