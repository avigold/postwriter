"""Planning orchestrator: coordinates agents from bootstrap through scene planning."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from postwriter.agents.architect import PremiseArchitect, SpineArchitect
from postwriter.agents.character_designer import CharacterDesigner
from postwriter.agents.chapter_planner import ChapterPlanner
from postwriter.agents.promise_seeder import PromiseSeeder
from postwriter.agents.scene_planner import ScenePlanner
from postwriter.agents.style_builder import StyleBuilder
from postwriter.canon.store import CanonStore
from postwriter.cli import display
from postwriter.context.loader import ContextFile
from postwriter.llm.client import LLMClient
from postwriter.models.core import Manuscript
from postwriter.prompts.loader import PromptLoader
from postwriter.types import AgentContext, ManuscriptStatus, PromiseType, SceneStatus

logger = logging.getLogger(__name__)


class PlanningOrchestrator:
    """Coordinates the full planning phase: premise → spine → characters →
    style → chapters → scenes → promises.

    Human checkpoints occur at premise approval and act structure approval.
    """

    def __init__(
        self,
        session: AsyncSession,
        llm: LLMClient,
        prompts: PromptLoader | None = None,
    ) -> None:
        self._session = session
        self._llm = llm
        self._prompts = prompts or PromptLoader()
        self._store = CanonStore(session)

    async def run(
        self,
        creative_brief: dict[str, Any],
        context_files: list[ContextFile] | None = None,
    ) -> Manuscript:
        """Run the full planning pipeline. Returns the manuscript with complete plan."""
        context_files = context_files or []
        user_context = self._prepare_user_context(context_files)

        # Step 1: Create manuscript
        display.section("Creating Manuscript")
        manuscript = await self._store.create_manuscript(
            title=creative_brief.get("genre", "Novel"),
            status=ManuscriptStatus.PLANNING,
        )
        await self._session.flush()
        await self._session.commit()
        display.success(f"Manuscript created: {manuscript.id}")

        # Step 2: Generate premise
        display.section("Generating Premise")
        premise_result = await self._generate_premise(
            manuscript, creative_brief, user_context
        )
        if not premise_result:
            display.error("Failed to generate premise")
            return manuscript

        # Update manuscript with premise
        manuscript.premise = premise_result["premise"]
        manuscript.controlling_design = premise_result["controlling_design"]
        await self._session.flush()
        await self._session.commit()

        # HUMAN CHECKPOINT 1: Premise approval
        display.show_premise(
            premise_result["premise"],
            premise_result["controlling_design"],
        )
        if not display.confirm("Approve this premise?"):
            display.warning("Premise rejected. You can re-run the bootstrap.")
            return manuscript

        # Step 3: Generate spine (act structure)
        display.section("Designing Act Structure")
        spine_result = await self._generate_spine(
            manuscript, creative_brief, user_context
        )
        if not spine_result:
            display.error("Failed to generate spine")
            return manuscript

        # HUMAN CHECKPOINT 2: Act structure approval
        display.show_act_structure(spine_result["acts"])
        if not display.confirm("Approve this act structure?"):
            display.warning("Act structure rejected.")
            return manuscript

        # Step 4: Create acts in DB
        display.section("Creating Act Structure")
        act_records = []
        for act_data in spine_result["acts"]:
            act = await self._store.create_act(
                manuscript.id,
                ordinal=act_data["ordinal"],
                name=act_data.get("name", f"Act {act_data['ordinal']}"),
                purpose=act_data.get("purpose", ""),
                emotional_arc=act_data.get("emotional_arc", {}),
            )
            act_records.append((act, act_data))
        await self._session.flush()
        await self._session.commit()
        display.success(f"Created {len(act_records)} acts")

        # Step 5: Design characters
        display.section("Designing Characters")
        cast_result = await self._design_characters(
            manuscript, creative_brief, user_context
        )
        if cast_result:
            char_records = []
            for char_data in cast_result.get("characters", []):
                char = await self._store.create_character(
                    manuscript.id,
                    name=char_data["name"],
                    aliases=char_data.get("aliases", []),
                    age=char_data.get("age"),
                    biography=char_data.get("biography", ""),
                    motives=char_data.get("motives", {}),
                    fears=char_data.get("fears", []),
                    desires=char_data.get("desires", []),
                    secrets=char_data.get("secrets", []),
                    social_position=char_data.get("social_position", ""),
                    speaking_traits=char_data.get("speaking_traits", {}),
                    movement_traits=char_data.get("movement_traits", {}),
                    recurring_gestures=char_data.get("recurring_gestures", []),
                    moral_constraints=char_data.get("moral_constraints", []),
                    arc_hypotheses={"hypothesis": char_data.get("arc_hypothesis", "")},
                    is_pov_character=char_data.get("is_pov_character", False),
                )
                char_records.append(char)
            await self._session.flush()
            display.show_characters([
                {"name": c.name, "biography": c.biography, "is_pov_character": c.is_pov_character,
                 "arc_hypothesis": c.arc_hypotheses.get("hypothesis", "")}
                for c in char_records
            ])
            await self._session.commit()
            display.success(f"Created {len(char_records)} characters")

        # Step 6: Build style profile
        display.section("Building Style Profile")
        style_result = await self._build_style(manuscript, creative_brief, user_context)
        if style_result:
            await self._store.create_style_profile(
                manuscript.id,
                is_default=True,
                voice_description=style_result.get("voice_description", ""),
                directness=style_result.get("directness", 0.5),
                subtext_target=style_result.get("subtext_target", 0.5),
                irony_target=style_result.get("irony_target", 0.3),
                lyricism_target=style_result.get("lyricism_target", 0.4),
                sentence_length_bands=style_result.get("sentence_length_bands", {}),
                dialogue_density_band=style_result.get("dialogue_density_band", {}),
                metaphor_density_band=style_result.get("metaphor_density_band", {}),
                fragment_tolerance=style_result.get("fragment_tolerance", 0.3),
                exposition_tolerance=style_result.get("exposition_tolerance", 0.4),
                abstraction_tolerance=style_result.get("abstraction_tolerance", 0.3),
                preferred_imagery_domains=style_result.get("preferred_imagery_domains", []),
                banned_imagery_domains=style_result.get("banned_imagery_domains", []),
                banned_phrases=style_result.get("banned_phrases", []),
                banned_moves=style_result.get("banned_moves", []),
                disfavoured_devices=style_result.get("disfavoured_devices", []),
                recurrence_caps=style_result.get("recurrence_caps", {}),
            )
            await self._session.flush()
            await self._session.commit()
            display.success("Style profile created")

        # Step 7: Plan chapters for each act
        display.section("Planning Chapters")
        all_chapters = []
        characters = await self._store.get_characters(manuscript.id)
        char_dicts = [
            {"name": c.name, "biography": c.biography, "is_pov": c.is_pov_character,
             "speaking_traits": c.speaking_traits}
            for c in characters
        ]

        for act, act_data in act_records:
            display.info(f"Planning chapters for Act {act.ordinal}: {act.name}")
            chapter_result = await self._plan_chapters(
                manuscript, act, act_data, char_dicts, creative_brief, user_context,
                preceding_chapters=all_chapters,
            )
            if chapter_result:
                for ch_data in chapter_result.get("chapters", []):
                    ch = await self._store.create_chapter(
                        manuscript.id,
                        act_id=act.id,
                        ordinal=ch_data["ordinal"] + len(all_chapters),
                        title=ch_data.get("title", ""),
                        function=ch_data.get("function", ""),
                        emotional_contour_target=ch_data.get("emotional_contour", {}),
                        opening_pressure=ch_data.get("opening_pressure", 0.5),
                        closing_pressure=ch_data.get("closing_pressure", 0.5),
                        rhythm_profile={},
                    )
                    ch_data["_id"] = str(ch.id)
                    ch_data["_scene_data"] = ch_data.get("scene_summaries", [])
                    all_chapters.append(ch_data)
                await self._session.flush()
                await self._session.commit()

        display.success(f"Planned {len(all_chapters)} chapters")

        # Step 8: Plan scenes for each chapter
        display.section("Planning Scenes")
        total_scenes = 0
        chapters_db = await self._store.get_all_chapters(manuscript.id)

        for i, ch_db in enumerate(chapters_db):
            ch_data = all_chapters[i] if i < len(all_chapters) else {}
            display.info(f"Planning scenes for Chapter {ch_db.ordinal}: {ch_db.title}")

            scene_result = await self._plan_scenes(
                manuscript, ch_db, ch_data, char_dicts, user_context
            )
            if scene_result:
                for sc_data in scene_result.get("scenes", []):
                    # Find POV character ID
                    pov_id = None
                    pov_name = sc_data.get("pov_character", "")
                    for c in characters:
                        if c.name.lower() == pov_name.lower():
                            pov_id = c.id
                            break

                    scene = await self._store.create_scene(
                        manuscript.id,
                        chapter_id=ch_db.id,
                        ordinal=sc_data.get("ordinal", total_scenes + 1),
                        pov_character_id=pov_id,
                        location=sc_data.get("location", ""),
                        time_marker=sc_data.get("time_marker", ""),
                        purpose=sc_data.get("purpose", ""),
                        conflict=sc_data.get("conflict", ""),
                        stakes=sc_data.get("stakes", ""),
                        revelation=sc_data.get("revelation"),
                        emotional_turn=sc_data.get("emotional_turn", ""),
                        dramatic_function=sc_data.get("dramatic_function", ""),
                        prohibited_moves=sc_data.get("prohibited_moves", []),
                        themes_touched=sc_data.get("themes_touched", []),
                        symbols_touched=sc_data.get("symbols_touched", []),
                        is_pivotal=sc_data.get("is_pivotal", False),
                        status=SceneStatus.PENDING,
                    )
                    total_scenes += 1
                await self._session.flush()
                await self._session.commit()

        display.success(f"Planned {total_scenes} scenes")

        # Step 9: Seed promises
        display.section("Identifying Narrative Promises")
        promise_result = await self._seed_promises(
            manuscript, spine_result, char_dicts
        )
        if promise_result:
            for p_data in promise_result.get("promises", []):
                try:
                    ptype = PromiseType(p_data.get("type", "plot"))
                except ValueError:
                    ptype = PromiseType.PLOT
                await self._store.create_promise(
                    manuscript.id,
                    type=ptype,
                    description=p_data.get("description", ""),
                    salience=p_data.get("salience", 0.5),
                )
            await self._session.flush()
            display.success(
                f"Identified {len(promise_result.get('promises', []))} narrative promises"
            )

        # Done
        manuscript.status = ManuscriptStatus.DRAFTING
        await self._session.flush()
        await self._session.commit()

        display.section("Planning Complete")
        display.success(
            f"Manuscript ready for drafting: {len(act_records)} acts, "
            f"{len(all_chapters)} chapters, {total_scenes} scenes"
        )

        return manuscript

    # ------------------------------------------------------------------
    # Agent call helpers
    # ------------------------------------------------------------------

    def _make_context(
        self,
        manuscript: Manuscript,
        user_context: list[dict[str, Any]],
        **extra: Any,
    ) -> AgentContext:
        return AgentContext(
            manuscript_id=str(manuscript.id),
            premise=manuscript.premise or "",
            controlling_design=manuscript.controlling_design or {},
            user_context=user_context,
            extra=extra,
        )

    async def _generate_premise(
        self,
        manuscript: Manuscript,
        brief: dict[str, Any],
        user_context: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        agent = PremiseArchitect(self._llm, self._prompts)
        ctx = self._make_context(manuscript, user_context, creative_brief=brief)
        result = await agent.execute(ctx)
        if result.success and result.parsed:
            parsed = result.parsed
            if hasattr(parsed, "model_dump"):
                return parsed.model_dump()
            return parsed if isinstance(parsed, dict) else None
        logger.error("Premise generation failed: %s", result.error)
        return None

    async def _generate_spine(
        self,
        manuscript: Manuscript,
        brief: dict[str, Any],
        user_context: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        agent = SpineArchitect(self._llm, self._prompts)
        ctx = self._make_context(
            manuscript, user_context,
            target_word_count=brief.get("target_word_count", 80000),
            target_chapters=brief.get("target_chapters", "30-40"),
        )
        result = await agent.execute(ctx)
        if result.success and result.parsed:
            parsed = result.parsed
            return parsed.model_dump() if hasattr(parsed, "model_dump") else parsed
        logger.error("Spine generation failed: %s", result.error)
        return None

    async def _design_characters(
        self,
        manuscript: Manuscript,
        brief: dict[str, Any],
        user_context: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        agent = CharacterDesigner(self._llm, self._prompts)
        ctx = self._make_context(
            manuscript, user_context,
            themes=brief.get("themes", []),
        )
        result = await agent.execute(ctx)
        if result.success and result.parsed:
            parsed = result.parsed
            return parsed.model_dump() if hasattr(parsed, "model_dump") else parsed
        logger.error("Character design failed: %s", result.error)
        return None

    async def _build_style(
        self,
        manuscript: Manuscript,
        brief: dict[str, Any],
        user_context: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        agent = StyleBuilder(self._llm, self._prompts)
        ctx = self._make_context(manuscript, user_context, creative_brief=brief)
        result = await agent.execute(ctx)
        if result.success and result.parsed:
            parsed = result.parsed
            return parsed.model_dump() if hasattr(parsed, "model_dump") else parsed
        logger.error("Style building failed: %s", result.error)
        return None

    async def _plan_chapters(
        self,
        manuscript: Manuscript,
        act: Any,
        act_data: dict[str, Any],
        characters: list[dict[str, Any]],
        brief: dict[str, Any],
        user_context: list[dict[str, Any]],
        preceding_chapters: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any] | None:
        agent = ChapterPlanner(self._llm, self._prompts)
        ctx = self._make_context(
            manuscript, user_context,
            act=act_data,
            themes=brief.get("themes", []),
            preceding_chapters=preceding_chapters or [],
        )
        ctx.characters = characters
        result = await agent.execute(ctx)
        if result.success and result.parsed:
            parsed = result.parsed
            return parsed.model_dump() if hasattr(parsed, "model_dump") else parsed
        logger.error("Chapter planning failed for act %s: %s", act.ordinal, result.error)
        return None

    async def _plan_scenes(
        self,
        manuscript: Manuscript,
        chapter: Any,
        ch_data: dict[str, Any],
        characters: list[dict[str, Any]],
        user_context: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        agent = ScenePlanner(self._llm, self._prompts)

        # Get style profile
        style = await self._store.get_default_style_profile(manuscript.id)
        style_dict = {}
        if style:
            style_dict = {"voice_description": style.voice_description}

        ctx = AgentContext(
            manuscript_id=str(manuscript.id),
            premise=manuscript.premise or "",
            chapter_brief={
                "title": chapter.title,
                "function": chapter.function,
                "emotional_contour": chapter.emotional_contour_target,
                "opening_pressure": chapter.opening_pressure,
                "closing_pressure": chapter.closing_pressure,
                "scene_count": ch_data.get("scene_count", 3),
                "scene_summaries": ch_data.get("scene_summaries", ch_data.get("_scene_data", [])),
                "pov_character": ch_data.get("pov_character", ""),
            },
            characters=characters,
            style_profile=style_dict,
            user_context=user_context,
        )
        result = await agent.execute(ctx)
        if result.success and result.parsed:
            parsed = result.parsed
            return parsed.model_dump() if hasattr(parsed, "model_dump") else parsed
        logger.error("Scene planning failed for chapter %s: %s", chapter.ordinal, result.error)
        return None

    async def _seed_promises(
        self,
        manuscript: Manuscript,
        spine_result: dict[str, Any],
        characters: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        agent = PromiseSeeder(self._llm, self._prompts)
        ctx = AgentContext(
            manuscript_id=str(manuscript.id),
            premise=manuscript.premise or "",
            controlling_design=manuscript.controlling_design or {},
            characters=characters,
            extra={"acts": spine_result.get("acts", [])},
        )
        result = await agent.execute(ctx)
        if result.success and result.parsed:
            parsed = result.parsed
            return parsed.model_dump() if hasattr(parsed, "model_dump") else parsed
        logger.error("Promise seeding failed: %s", result.error)
        return None

    @staticmethod
    def _prepare_user_context(context_files: list[ContextFile]) -> list[dict[str, Any]]:
        return [
            {
                "name": cf.name,
                "type": cf.context_type.value,
                "content": cf.content,
                "is_image": cf.is_image,
            }
            for cf in context_files
            if not cf.is_image  # Images handled separately via vision
        ]
