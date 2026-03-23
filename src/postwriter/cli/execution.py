"""CLI execution: runs the drafting phase with progress display."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from postwriter.cli import display
from postwriter.config import OrchestratorSettings
from postwriter.context.loader import ContextFile
from postwriter.llm.client import LLMClient
from postwriter.orchestrator.engine import FictionOrchestrator
from postwriter.prompts.loader import PromptLoader


async def run_drafting(
    session: AsyncSession,
    llm: LLMClient,
    manuscript_id: uuid.UUID,
    context_files: list[ContextFile] | None = None,
    settings: OrchestratorSettings | None = None,
) -> None:
    """Run the full drafting phase for a manuscript."""
    display.banner()
    display.section("Drafting Phase")

    orchestrator = FictionOrchestrator(
        session=session,
        llm=llm,
        settings=settings,
        context_files=context_files,
    )

    await orchestrator.run(manuscript_id)
