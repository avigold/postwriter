"""Canon slicer: builds token-budget-aware context windows for agents."""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from postwriter.config import OrchestratorSettings
from postwriter.models.characters import Character, CharacterSceneState
from postwriter.models.core import Chapter, Manuscript, Scene, SceneDraft
from postwriter.models.narrative import Promise
from postwriter.models.style import StyleProfile
from postwriter.types import AgentContext, PromiseStatus, SceneStatus


class CanonSlicer:
    """Builds context windows for agents from the canonical data store.

    The slicer assembles only the data an agent needs, keeping total
    token usage within budget. Priority order for trimming:
    1. Remove oldest rolling-window scenes
    2. Shorten character biographies
    3. Remove low-priority promise details
    Never remove: scene brief, immediately preceding scene, style profile,
    character states for present characters.
    """

    def __init__(
        self,
        session: AsyncSession,
        settings: OrchestratorSettings | None = None,
    ) -> None:
        self._session = session
        self._settings = settings or OrchestratorSettings()

    async def build_scene_context(
        self,
        manuscript_id: uuid.UUID,
        scene_id: uuid.UUID,
    ) -> AgentContext:
        """Build a full context for scene-level agents (writer, critics, repair)."""
        scene = await self._session.get(Scene, scene_id)
        if not scene:
            return AgentContext(manuscript_id=str(manuscript_id))

        manuscript = await self._session.get(Manuscript, manuscript_id)
        chapter = await self._session.get(Chapter, scene.chapter_id)

        # Style profile
        style_stmt = (
            select(StyleProfile)
            .where(StyleProfile.manuscript_id == manuscript_id)
            .where(StyleProfile.is_default.is_(True))
        )
        style_result = await self._session.execute(style_stmt)
        style_profile = style_result.scalar_one_or_none()

        # Characters in this scene's chapter (via POV and scene states)
        char_states = await self._get_character_states(scene_id)
        character_ids = [cs.character_id for cs in char_states]
        if scene.pov_character_id and scene.pov_character_id not in character_ids:
            character_ids.append(scene.pov_character_id)

        characters = []
        for cid in character_ids:
            char = await self._session.get(Character, cid)
            if char:
                characters.append(self._serialize_character(char))

        # Preceding scenes (rolling window)
        preceding = await self._get_preceding_scenes(
            scene.chapter_id, scene.ordinal, self._settings.rolling_window_scenes
        )

        # Open promises
        promises = await self._get_open_promises(manuscript_id)

        return AgentContext(
            manuscript_id=str(manuscript_id),
            premise=manuscript.premise if manuscript else "",
            controlling_design=manuscript.controlling_design if manuscript else {},
            style_profile=self._serialize_style(style_profile) if style_profile else {},
            chapter_brief=self._serialize_chapter(chapter) if chapter else {},
            scene_brief=self._serialize_scene(scene),
            characters=characters,
            character_states=[self._serialize_char_state(cs) for cs in char_states],
            preceding_scenes=preceding,
            open_promises=[self._serialize_promise(p) for p in promises],
        )

    async def build_planning_context(
        self,
        manuscript_id: uuid.UUID,
    ) -> AgentContext:
        """Build context for planning agents (architect, chapter/scene planners)."""
        manuscript = await self._session.get(Manuscript, manuscript_id)
        if not manuscript:
            return AgentContext(manuscript_id=str(manuscript_id))

        characters = []
        char_stmt = select(Character).where(Character.manuscript_id == manuscript_id)
        char_result = await self._session.execute(char_stmt)
        for char in char_result.scalars().all():
            characters.append(self._serialize_character(char))

        style_stmt = (
            select(StyleProfile)
            .where(StyleProfile.manuscript_id == manuscript_id)
            .where(StyleProfile.is_default.is_(True))
        )
        style_result = await self._session.execute(style_stmt)
        style_profile = style_result.scalar_one_or_none()

        return AgentContext(
            manuscript_id=str(manuscript_id),
            premise=manuscript.premise,
            controlling_design=manuscript.controlling_design,
            style_profile=self._serialize_style(style_profile) if style_profile else {},
            characters=characters,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _get_character_states(self, scene_id: uuid.UUID) -> list[CharacterSceneState]:
        stmt = select(CharacterSceneState).where(CharacterSceneState.scene_id == scene_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def _get_preceding_scenes(
        self, chapter_id: uuid.UUID, current_ordinal: int, count: int
    ) -> list[dict[str, Any]]:
        stmt = (
            select(Scene)
            .where(Scene.chapter_id == chapter_id)
            .where(Scene.ordinal < current_ordinal)
            .where(Scene.status == SceneStatus.ACCEPTED)
            .order_by(Scene.ordinal.desc())
            .limit(count)
        )
        result = await self._session.execute(stmt)
        scenes = list(result.scalars().all())

        preceding = []
        for s in reversed(scenes):
            scene_data = self._serialize_scene(s)
            if s.accepted_draft_id:
                draft = await self._session.get(SceneDraft, s.accepted_draft_id)
                if draft:
                    scene_data["accepted_prose"] = draft.prose
            preceding.append(scene_data)
        return preceding

    async def _get_open_promises(self, manuscript_id: uuid.UUID) -> list[Promise]:
        stmt = (
            select(Promise)
            .where(Promise.manuscript_id == manuscript_id)
            .where(Promise.status.in_([PromiseStatus.OPEN, PromiseStatus.MATURING]))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def _serialize_character(char: Character) -> dict[str, Any]:
        return {
            "id": str(char.id),
            "name": char.name,
            "aliases": char.aliases,
            "age": char.age,
            "biography": char.biography,
            "motives": char.motives,
            "fears": char.fears,
            "desires": char.desires,
            "social_position": char.social_position,
            "speaking_traits": char.speaking_traits,
            "is_pov": char.is_pov_character,
        }

    @staticmethod
    def _serialize_char_state(cs: CharacterSceneState) -> dict[str, Any]:
        return {
            "character_id": str(cs.character_id),
            "scene_id": str(cs.scene_id),
            "knowledge_state": cs.knowledge_state,
            "emotional_state": cs.emotional_state,
            "intention_state": cs.intention_state,
            "unresolved_pressures": cs.unresolved_pressures,
            "arc_position": cs.arc_position,
        }

    @staticmethod
    def _serialize_scene(scene: Scene) -> dict[str, Any]:
        return {
            "id": str(scene.id),
            "ordinal": scene.ordinal,
            "pov_character_id": str(scene.pov_character_id) if scene.pov_character_id else None,
            "location": scene.location,
            "time_marker": scene.time_marker,
            "purpose": scene.purpose,
            "conflict": scene.conflict,
            "stakes": scene.stakes,
            "revelation": scene.revelation,
            "emotional_turn": scene.emotional_turn,
            "dramatic_function": scene.dramatic_function,
            "expected_stylistic_profile": scene.expected_stylistic_profile,
            "prohibited_moves": scene.prohibited_moves,
            "themes_touched": scene.themes_touched,
            "symbols_touched": scene.symbols_touched,
            "is_pivotal": scene.is_pivotal,
        }

    @staticmethod
    def _serialize_chapter(chapter: Chapter) -> dict[str, Any]:
        return {
            "id": str(chapter.id),
            "ordinal": chapter.ordinal,
            "title": chapter.title,
            "function": chapter.function,
            "emotional_contour_target": chapter.emotional_contour_target,
            "opening_pressure": chapter.opening_pressure,
            "closing_pressure": chapter.closing_pressure,
            "rhythm_profile": chapter.rhythm_profile,
        }

    @staticmethod
    def _serialize_style(sp: StyleProfile) -> dict[str, Any]:
        return {
            "voice_description": sp.voice_description,
            "directness": sp.directness,
            "subtext_target": sp.subtext_target,
            "irony_target": sp.irony_target,
            "lyricism_target": sp.lyricism_target,
            "sentence_length_bands": sp.sentence_length_bands,
            "dialogue_density_band": sp.dialogue_density_band,
            "metaphor_density_band": sp.metaphor_density_band,
            "fragment_tolerance": sp.fragment_tolerance,
            "preferred_imagery_domains": sp.preferred_imagery_domains,
            "banned_imagery_domains": sp.banned_imagery_domains,
            "banned_phrases": sp.banned_phrases,
            "banned_moves": sp.banned_moves,
            "disfavoured_devices": sp.disfavoured_devices,
            "recurrence_caps": sp.recurrence_caps,
        }

    @staticmethod
    def _serialize_promise(p: Promise) -> dict[str, Any]:
        return {
            "id": str(p.id),
            "type": p.type.value,
            "description": p.description,
            "salience": p.salience,
            "status": p.status.value,
        }

    @staticmethod
    def _estimate_tokens(data: Any) -> int:
        """Rough token estimate: ~4 chars per token."""
        return len(json.dumps(data, default=str)) // 4
