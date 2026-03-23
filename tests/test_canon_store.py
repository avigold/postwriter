"""Tests for the CanonStore CRUD operations."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from postwriter.canon.store import CanonStore
from postwriter.types import PromiseStatus, PromiseType


@pytest.mark.asyncio
async def test_create_and_get_manuscript(session: AsyncSession):
    store = CanonStore(session)
    m = await store.create_manuscript(title="Test Novel", premise="A test premise.")
    await session.flush()

    retrieved = await store.get_manuscript(m.id)
    assert retrieved is not None
    assert retrieved.title == "Test Novel"


@pytest.mark.asyncio
async def test_create_acts_and_chapters(session: AsyncSession):
    store = CanonStore(session)
    m = await store.create_manuscript(title="Structured")
    await session.flush()

    act = await store.create_act(m.id, ordinal=1, name="Act I")
    await session.flush()

    ch = await store.create_chapter(m.id, act_id=act.id, ordinal=1, title="Ch 1")
    await session.flush()

    chapters = await store.get_chapters(act.id)
    assert len(chapters) == 1
    assert chapters[0].title == "Ch 1"


@pytest.mark.asyncio
async def test_create_scene_and_drafts(session: AsyncSession):
    store = CanonStore(session)
    m = await store.create_manuscript(title="Scene Test")
    await session.flush()

    act = await store.create_act(m.id, ordinal=1)
    await session.flush()

    ch = await store.create_chapter(m.id, act_id=act.id, ordinal=1)
    await session.flush()

    scene = await store.create_scene(m.id, chapter_id=ch.id, ordinal=1, purpose="Test scene")
    await session.flush()

    draft = await store.create_draft(
        m.id,
        scene_id=scene.id,
        branch_label="default",
        prose="She walked into the room.",
    )
    await session.flush()

    drafts = await store.get_drafts(scene.id)
    assert len(drafts) == 1
    assert drafts[0].word_count == 5


@pytest.mark.asyncio
async def test_create_character(session: AsyncSession):
    store = CanonStore(session)
    m = await store.create_manuscript(title="Char Test")
    await session.flush()

    char = await store.create_character(
        m.id,
        name="Marcus",
        biography="A weary detective.",
        fears=["failure"],
    )
    await session.flush()

    chars = await store.get_characters(m.id)
    assert len(chars) == 1
    assert chars[0].name == "Marcus"


@pytest.mark.asyncio
async def test_create_promise(session: AsyncSession):
    store = CanonStore(session)
    m = await store.create_manuscript(title="Promise Test")
    await session.flush()

    p = await store.create_promise(
        m.id,
        type=PromiseType.EMOTIONAL,
        description="The grief must surface.",
        salience=0.9,
    )
    await session.flush()

    promises = await store.get_promises(m.id)
    assert len(promises) == 1
    assert promises[0].type == PromiseType.EMOTIONAL


@pytest.mark.asyncio
async def test_create_theme(session: AsyncSession):
    store = CanonStore(session)
    m = await store.create_manuscript(title="Theme Test")
    await session.flush()

    t = await store.create_theme(
        m.id,
        name="Betrayal",
        description="Trust broken by those closest.",
    )
    await session.flush()

    themes = await store.get_themes(m.id)
    assert len(themes) == 1
    assert themes[0].name == "Betrayal"


@pytest.mark.asyncio
async def test_create_style_profile(session: AsyncSession):
    store = CanonStore(session)
    m = await store.create_manuscript(title="Style Test")
    await session.flush()

    sp = await store.create_style_profile(
        m.id,
        is_default=True,
        voice_description="Sparse and controlled.",
        banned_phrases=["very", "really"],
    )
    await session.flush()

    default_sp = await store.get_default_style_profile(m.id)
    assert default_sp is not None
    assert default_sp.voice_description == "Sparse and controlled."
