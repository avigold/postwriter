"""Tests for export system."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from postwriter.canon.store import CanonStore
from postwriter.export.markdown import export_markdown
from postwriter.export.json_export import export_json
from postwriter.types import BranchStatus, SceneStatus


async def _create_test_manuscript(session: AsyncSession) -> uuid.UUID:
    """Create a minimal manuscript for export testing."""
    store = CanonStore(session)
    m = await store.create_manuscript(title="Export Test Novel", premise="A test premise.")
    await session.flush()

    act = await store.create_act(m.id, ordinal=1, name="Act One")
    await session.flush()

    ch = await store.create_chapter(m.id, act_id=act.id, ordinal=1, title="The Beginning")
    await session.flush()

    scene = await store.create_scene(
        m.id, chapter_id=ch.id, ordinal=1,
        purpose="Open the story", conflict="Internal tension",
    )
    await session.flush()

    draft = await store.create_draft(
        m.id, scene_id=scene.id,
        branch_label="restrained_subtext_heavy",
        prose="The harbor lay flat under a low sky. Elena walked toward the terminal.",
        branch_status=BranchStatus.SELECTED,
    )
    await session.flush()

    await store.update_scene_status(
        m.id, scene.id,
        status=SceneStatus.ACCEPTED,
        accepted_draft_id=draft.id,
    )
    await session.flush()

    await store.create_character(m.id, name="Elena", biography="A retired professor.")
    await store.create_theme(m.id, name="Isolation", description="The cost of distance.")
    await session.flush()

    return m.id


@pytest.mark.asyncio
async def test_export_markdown(session: AsyncSession):
    mid = await _create_test_manuscript(session)
    text = await export_markdown(session, mid)

    assert "# Export Test Novel" in text
    assert "## The Beginning" in text
    assert "Elena walked" in text
    assert "words" in text.lower()


@pytest.mark.asyncio
async def test_export_json(session: AsyncSession):
    mid = await _create_test_manuscript(session)
    data = await export_json(session, mid)

    assert data["manuscript"]["title"] == "Export Test Novel"
    assert len(data["chapters"]) == 1
    assert len(data["characters"]) >= 1
    assert data["characters"][0]["name"] == "Elena"
    assert len(data["themes"]) >= 1

    # Check scene/draft structure
    scenes = data["chapters"][0]["scenes"]
    assert len(scenes) == 1
    assert len(scenes[0]["drafts"]) >= 1


@pytest.mark.asyncio
async def test_export_nonexistent(session: AsyncSession):
    fake_id = uuid.uuid4()
    text = await export_markdown(session, fake_id)
    assert text == ""

    data = await export_json(session, fake_id)
    assert data == {}
