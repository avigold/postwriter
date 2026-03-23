"""CRUD operations for all canonical entities."""

from __future__ import annotations

import uuid
from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from postwriter.canon.events import EventLogger
from postwriter.models.base import Base
from postwriter.models.characters import Character, CharacterRelationship, CharacterSceneState
from postwriter.models.core import Act, Chapter, Manuscript, Scene, SceneDraft
from postwriter.models.narrative import Promise, Theme, TimelineEvent
from postwriter.models.style import StyleProfile

T = TypeVar("T", bound=Base)


class CanonStore:
    """Provides CRUD operations for all canonical entities with event logging."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._events = EventLogger(session)

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------

    async def _get(self, model: type[T], id: uuid.UUID) -> T | None:
        return await self._session.get(model, id)

    async def _create(
        self,
        entity: Base,
        manuscript_id: uuid.UUID,
        entity_type: str,
    ) -> Base:
        self._session.add(entity)
        await self._session.flush()
        await self._events.record(
            manuscript_id=manuscript_id,
            entity_type=entity_type,
            entity_id=entity.id,  # type: ignore[attr-defined]
            event_type="created",
            payload={"type": entity_type},
        )
        return entity

    # ------------------------------------------------------------------
    # Manuscript
    # ------------------------------------------------------------------

    async def create_manuscript(self, **kwargs: Any) -> Manuscript:
        m = Manuscript(**kwargs)
        self._session.add(m)
        await self._session.flush()
        await self._events.record(
            manuscript_id=m.id,
            entity_type="manuscript",
            entity_id=m.id,
            event_type="created",
            payload={"title": m.title},
        )
        return m

    async def get_manuscript(self, id: uuid.UUID) -> Manuscript | None:
        return await self._get(Manuscript, id)

    async def get_manuscript_full(self, id: uuid.UUID) -> Manuscript | None:
        stmt = (
            select(Manuscript)
            .where(Manuscript.id == id)
            .options(
                selectinload(Manuscript.acts).selectinload(Act.chapters).selectinload(Chapter.scenes),
                selectinload(Manuscript.characters),
                selectinload(Manuscript.themes),
                selectinload(Manuscript.promises),
                selectinload(Manuscript.style_profiles),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Acts
    # ------------------------------------------------------------------

    async def create_act(self, manuscript_id: uuid.UUID, **kwargs: Any) -> Act:
        act = Act(manuscript_id=manuscript_id, **kwargs)
        return await self._create(act, manuscript_id, "act")  # type: ignore[return-value]

    async def get_acts(self, manuscript_id: uuid.UUID) -> list[Act]:
        stmt = (
            select(Act)
            .where(Act.manuscript_id == manuscript_id)
            .order_by(Act.ordinal)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Chapters
    # ------------------------------------------------------------------

    async def create_chapter(self, manuscript_id: uuid.UUID, **kwargs: Any) -> Chapter:
        ch = Chapter(manuscript_id=manuscript_id, **kwargs)
        return await self._create(ch, manuscript_id, "chapter")  # type: ignore[return-value]

    async def get_chapters(self, act_id: uuid.UUID) -> list[Chapter]:
        stmt = select(Chapter).where(Chapter.act_id == act_id).order_by(Chapter.ordinal)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_chapters(self, manuscript_id: uuid.UUID) -> list[Chapter]:
        stmt = (
            select(Chapter)
            .where(Chapter.manuscript_id == manuscript_id)
            .order_by(Chapter.ordinal)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Scenes
    # ------------------------------------------------------------------

    async def create_scene(self, manuscript_id: uuid.UUID, **kwargs: Any) -> Scene:
        scene = Scene(**kwargs)
        self._session.add(scene)
        await self._session.flush()
        # Infer manuscript_id from chapter
        await self._events.record(
            manuscript_id=manuscript_id,
            entity_type="scene",
            entity_id=scene.id,
            event_type="created",
            payload={"chapter_id": str(kwargs.get("chapter_id", ""))},
        )
        return scene

    async def get_scene(self, id: uuid.UUID) -> Scene | None:
        return await self._get(Scene, id)

    async def get_scenes(self, chapter_id: uuid.UUID) -> list[Scene]:
        stmt = select(Scene).where(Scene.chapter_id == chapter_id).order_by(Scene.ordinal)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_scene_status(
        self, manuscript_id: uuid.UUID, scene_id: uuid.UUID, **kwargs: Any
    ) -> None:
        scene = await self._get(Scene, scene_id)
        if scene:
            for k, v in kwargs.items():
                setattr(scene, k, v)
            await self._session.flush()
            # Serialize payload values for JSON storage
            safe_payload = {
                k: str(v) if isinstance(v, (uuid.UUID,)) else
                   v.value if hasattr(v, "value") else v
                for k, v in kwargs.items()
            }
            await self._events.record(
                manuscript_id=manuscript_id,
                entity_type="scene",
                entity_id=scene_id,
                event_type="updated",
                payload=safe_payload,
            )

    # ------------------------------------------------------------------
    # Scene Drafts
    # ------------------------------------------------------------------

    async def create_draft(self, manuscript_id: uuid.UUID, **kwargs: Any) -> SceneDraft:
        draft = SceneDraft(**kwargs)
        draft.word_count = len(draft.prose.split()) if draft.prose else 0
        self._session.add(draft)
        await self._session.flush()
        await self._events.record(
            manuscript_id=manuscript_id,
            entity_type="scene_draft",
            entity_id=draft.id,
            event_type="created",
            payload={
                "scene_id": str(kwargs.get("scene_id", "")),
                "branch_label": draft.branch_label,
                "word_count": draft.word_count,
            },
        )
        return draft

    async def get_drafts(self, scene_id: uuid.UUID) -> list[SceneDraft]:
        stmt = select(SceneDraft).where(SceneDraft.scene_id == scene_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Characters
    # ------------------------------------------------------------------

    async def create_character(self, manuscript_id: uuid.UUID, **kwargs: Any) -> Character:
        char = Character(manuscript_id=manuscript_id, **kwargs)
        return await self._create(char, manuscript_id, "character")  # type: ignore[return-value]

    async def get_characters(self, manuscript_id: uuid.UUID) -> list[Character]:
        stmt = select(Character).where(Character.manuscript_id == manuscript_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_character(self, id: uuid.UUID) -> Character | None:
        return await self._get(Character, id)

    # ------------------------------------------------------------------
    # Character Scene States
    # ------------------------------------------------------------------

    async def set_character_state(
        self, manuscript_id: uuid.UUID, **kwargs: Any
    ) -> CharacterSceneState:
        state = CharacterSceneState(**kwargs)
        self._session.add(state)
        await self._session.flush()
        await self._events.record(
            manuscript_id=manuscript_id,
            entity_type="character_scene_state",
            entity_id=state.id,
            event_type="created",
            payload={
                "character_id": str(kwargs.get("character_id", "")),
                "scene_id": str(kwargs.get("scene_id", "")),
            },
        )
        return state

    async def get_character_states_for_scene(
        self, scene_id: uuid.UUID
    ) -> list[CharacterSceneState]:
        stmt = select(CharacterSceneState).where(CharacterSceneState.scene_id == scene_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Promises
    # ------------------------------------------------------------------

    async def create_promise(self, manuscript_id: uuid.UUID, **kwargs: Any) -> Promise:
        p = Promise(manuscript_id=manuscript_id, **kwargs)
        return await self._create(p, manuscript_id, "promise")  # type: ignore[return-value]

    async def get_promises(
        self, manuscript_id: uuid.UUID, status: str | None = None
    ) -> list[Promise]:
        stmt = select(Promise).where(Promise.manuscript_id == manuscript_id)
        if status:
            stmt = stmt.where(Promise.status == status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Themes
    # ------------------------------------------------------------------

    async def create_theme(self, manuscript_id: uuid.UUID, **kwargs: Any) -> Theme:
        t = Theme(manuscript_id=manuscript_id, **kwargs)
        return await self._create(t, manuscript_id, "theme")  # type: ignore[return-value]

    async def get_themes(self, manuscript_id: uuid.UUID) -> list[Theme]:
        stmt = select(Theme).where(Theme.manuscript_id == manuscript_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Style Profiles
    # ------------------------------------------------------------------

    async def create_style_profile(
        self, manuscript_id: uuid.UUID, **kwargs: Any
    ) -> StyleProfile:
        sp = StyleProfile(manuscript_id=manuscript_id, **kwargs)
        return await self._create(sp, manuscript_id, "style_profile")  # type: ignore[return-value]

    async def get_default_style_profile(
        self, manuscript_id: uuid.UUID
    ) -> StyleProfile | None:
        stmt = (
            select(StyleProfile)
            .where(StyleProfile.manuscript_id == manuscript_id)
            .where(StyleProfile.is_default.is_(True))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Timeline Events
    # ------------------------------------------------------------------

    async def create_timeline_event(
        self, manuscript_id: uuid.UUID, **kwargs: Any
    ) -> TimelineEvent:
        te = TimelineEvent(manuscript_id=manuscript_id, **kwargs)
        return await self._create(te, manuscript_id, "timeline_event")  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Character Relationships
    # ------------------------------------------------------------------

    async def create_relationship(
        self, manuscript_id: uuid.UUID, **kwargs: Any
    ) -> CharacterRelationship:
        rel = CharacterRelationship(manuscript_id=manuscript_id, **kwargs)
        return await self._create(rel, manuscript_id, "character_relationship")  # type: ignore[return-value]
