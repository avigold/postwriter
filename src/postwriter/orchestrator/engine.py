"""FictionOrchestrator: the main engine that coordinates the full novel generation."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from postwriter.canon.slicer import CanonSlicer
from postwriter.canon.store import CanonStore
from postwriter.cli import display
from postwriter.config import OrchestratorSettings
from postwriter.context.loader import ContextFile
from postwriter.llm.client import LLMClient
from postwriter.orchestrator.policies import ScenePolicy
from postwriter.orchestrator.scene_loop import SceneLoop
from postwriter.prompts.loader import PromptLoader
from postwriter.types import ManuscriptStatus, SceneStatus

logger = logging.getLogger(__name__)


class FictionOrchestrator:
    """Top-level orchestrator: processes all chapters and scenes for a manuscript.

    Execution flow:
    1. Load manuscript state
    2. For each chapter:
       a. For each scene in chapter:
          - Build context via canon slicer
          - Run scene loop (branch → validate → repair → select)
          - Commit accepted draft
    3. (Phase 6) Run global revision passes
    4. Export
    """

    def __init__(
        self,
        session: AsyncSession,
        llm: LLMClient,
        prompts: PromptLoader | None = None,
        settings: OrchestratorSettings | None = None,
        context_files: list[ContextFile] | None = None,
    ) -> None:
        self._session = session
        self._llm = llm
        self._prompts = prompts or PromptLoader()
        self._settings = settings or OrchestratorSettings()
        self._store = CanonStore(session)
        self._slicer = CanonSlicer(session, self._settings)
        self._policy = ScenePolicy.from_settings(self._settings)
        self._context_files = context_files or []
        self._scene_loop = SceneLoop(session, llm, prompts, self._policy)

    async def run(self, manuscript_id: uuid.UUID) -> None:
        """Run the full drafting phase for a manuscript."""
        manuscript = await self._store.get_manuscript(manuscript_id)
        if not manuscript:
            display.error(f"Manuscript {manuscript_id} not found")
            return

        if manuscript.status != ManuscriptStatus.DRAFTING:
            display.warning(
                f"Manuscript is in {manuscript.status.value} state, expected DRAFTING"
            )

        display.section("Beginning Drafting Phase")
        display.info(f"Manuscript: {manuscript.title} ({manuscript_id})")

        # Get all chapters in order
        chapters = await self._store.get_all_chapters(manuscript_id)
        total_chapters = len(chapters)
        total_scenes_processed = 0
        total_words = 0

        for ch_idx, chapter in enumerate(chapters):
            display.section(
                f"Chapter {chapter.ordinal}: {chapter.title} "
                f"({ch_idx + 1}/{total_chapters})"
            )

            scenes = await self._store.get_scenes(chapter.id)
            for sc_idx, scene in enumerate(scenes):
                if scene.status == SceneStatus.ACCEPTED:
                    display.info(f"  Scene {scene.ordinal}: already accepted, skipping")
                    continue

                display.info(
                    f"  Scene {scene.ordinal}: {scene.purpose[:60]}..."
                    if len(scene.purpose) > 60
                    else f"  Scene {scene.ordinal}: {scene.purpose}"
                )

                # Build context for this scene
                context = await self._slicer.build_scene_context(
                    manuscript_id, scene.id
                )

                # Add user context files
                if self._context_files:
                    context.user_context = [
                        {
                            "name": cf.name,
                            "type": cf.context_type.value,
                            "content": cf.content,
                        }
                        for cf in self._context_files
                        if not cf.is_image
                    ]

                # Process scene through the loop
                result = await self._scene_loop.process_scene(
                    manuscript_id=manuscript_id,
                    scene_id=scene.id,
                    context=context,
                    is_pivotal=scene.is_pivotal,
                )

                if result:
                    total_scenes_processed += 1
                    total_words += result.word_count

                # Progress update
                display.show_progress(
                    "Drafting",
                    total_scenes_processed,
                    sum(len(await self._store.get_scenes(ch.id)) for ch in chapters[:ch_idx + 1]),
                    detail=f"~{total_words:,} words",
                )

            await self._session.flush()
            display.info("")  # Newline after progress bar

        # Update manuscript status
        manuscript.status = ManuscriptStatus.REVISING
        await self._session.flush()
        await self._session.commit()

        display.section("Drafting Complete")
        display.success(
            f"Processed {total_scenes_processed} scenes, ~{total_words:,} words"
        )
        display.info(
            f"Token usage: {self._llm.budget.summary()}"
        )
