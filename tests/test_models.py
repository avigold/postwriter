"""Tests for SQLAlchemy model creation and relationships."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from postwriter.models.characters import Character
from postwriter.models.core import Act, Chapter, Manuscript, Scene, SceneDraft
from postwriter.models.narrative import Promise, Theme
from postwriter.models.style import StyleProfile
from postwriter.types import BranchStatus, ManuscriptStatus, PromiseStatus, PromiseType


@pytest.mark.asyncio
async def test_create_manuscript(session: AsyncSession):
    m = Manuscript(title="Test Novel", premise="A story about testing.")
    session.add(m)
    await session.flush()

    assert m.id is not None
    assert m.title == "Test Novel"
    assert m.status == ManuscriptStatus.BOOTSTRAPPING


@pytest.mark.asyncio
async def test_manuscript_with_acts_and_chapters(session: AsyncSession):
    m = Manuscript(title="Structured Novel")
    session.add(m)
    await session.flush()

    act = Act(manuscript_id=m.id, ordinal=1, name="Act One", purpose="Setup")
    session.add(act)
    await session.flush()

    ch = Chapter(
        manuscript_id=m.id,
        act_id=act.id,
        ordinal=1,
        title="Chapter One",
        function="Introduce protagonist",
    )
    session.add(ch)
    await session.flush()

    scene = Scene(
        chapter_id=ch.id,
        ordinal=1,
        location="A dark room",
        purpose="Establish mood",
        conflict="Unknown threat",
    )
    session.add(scene)
    await session.flush()

    assert scene.id is not None
    assert scene.chapter_id == ch.id


@pytest.mark.asyncio
async def test_scene_drafts(session: AsyncSession):
    m = Manuscript(title="Draft Test")
    session.add(m)
    await session.flush()

    act = Act(manuscript_id=m.id, ordinal=1)
    session.add(act)
    await session.flush()

    ch = Chapter(manuscript_id=m.id, act_id=act.id, ordinal=1)
    session.add(ch)
    await session.flush()

    scene = Scene(chapter_id=ch.id, ordinal=1)
    session.add(scene)
    await session.flush()

    draft1 = SceneDraft(
        scene_id=scene.id,
        branch_label="restrained_subtext_heavy",
        prose="The room was silent. Too silent.",
        word_count=6,
    )
    draft2 = SceneDraft(
        scene_id=scene.id,
        branch_label="lyrical_image_forward",
        prose="Light fell through the window like water through a sieve.",
        word_count=11,
    )
    session.add_all([draft1, draft2])
    await session.flush()

    assert draft1.branch_status == BranchStatus.ACTIVE
    assert draft2.branch_status == BranchStatus.ACTIVE


@pytest.mark.asyncio
async def test_character_creation(session: AsyncSession):
    m = Manuscript(title="Character Test")
    session.add(m)
    await session.flush()

    char = Character(
        manuscript_id=m.id,
        name="Elena Voss",
        aliases=["The Professor", "E.V."],
        biography="A former academic turned investigator.",
        motives={"primary": "truth", "secondary": "redemption"},
        fears=["irrelevance", "betrayal"],
        desires=["understanding", "justice"],
        speaking_traits={"pattern": "precise", "vocabulary": "academic"},
        is_pov_character=True,
    )
    session.add(char)
    await session.flush()

    assert char.id is not None
    assert char.aliases == ["The Professor", "E.V."]
    assert char.motives["primary"] == "truth"


@pytest.mark.asyncio
async def test_promise_creation(session: AsyncSession):
    m = Manuscript(title="Promise Test")
    session.add(m)
    await session.flush()

    promise = Promise(
        manuscript_id=m.id,
        type=PromiseType.PLOT,
        description="The locked box in the attic must be opened.",
        salience=0.8,
        status=PromiseStatus.OPEN,
    )
    session.add(promise)
    await session.flush()

    assert promise.id is not None
    assert promise.type == PromiseType.PLOT
    assert promise.status == PromiseStatus.OPEN


@pytest.mark.asyncio
async def test_theme_creation(session: AsyncSession):
    m = Manuscript(title="Theme Test")
    session.add(m)
    await session.flush()

    theme = Theme(
        manuscript_id=m.id,
        name="Isolation",
        description="The cost of self-imposed distance.",
        associated_symbols=["empty rooms", "unanswered phones"],
        preferred_embodiment_modes=["situational", "dialogic absence"],
        overstatement_risk=0.3,
    )
    session.add(theme)
    await session.flush()

    assert theme.associated_symbols == ["empty rooms", "unanswered phones"]


@pytest.mark.asyncio
async def test_style_profile_creation(session: AsyncSession):
    m = Manuscript(title="Style Test")
    session.add(m)
    await session.flush()

    sp = StyleProfile(
        manuscript_id=m.id,
        is_default=True,
        voice_description="Terse, observational, with occasional lyrical breaks.",
        directness=0.7,
        subtext_target=0.6,
        lyricism_target=0.3,
        banned_phrases=["it was as if", "suddenly"],
        preferred_imagery_domains=["architecture", "weather", "glass"],
    )
    session.add(sp)
    await session.flush()

    assert sp.is_default is True
    assert "suddenly" in sp.banned_phrases
