"""Tests for the append-only event logger."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from postwriter.canon.events import EventLogger
from postwriter.models.core import Manuscript


@pytest.mark.asyncio
async def test_record_event(session: AsyncSession):
    m = Manuscript(title="Event Test")
    session.add(m)
    await session.flush()

    logger = EventLogger(session)
    event = await logger.record(
        manuscript_id=m.id,
        entity_type="manuscript",
        entity_id=m.id,
        event_type="created",
        payload={"title": "Event Test"},
    )
    await session.flush()

    assert event.sequence == 1
    assert event.entity_type == "manuscript"
    assert event.payload["title"] == "Event Test"


@pytest.mark.asyncio
async def test_sequence_increments(session: AsyncSession):
    m = Manuscript(title="Seq Test")
    session.add(m)
    await session.flush()

    logger = EventLogger(session)
    e1 = await logger.record(m.id, "test", m.id, "first")
    await session.flush()
    e2 = await logger.record(m.id, "test", m.id, "second")
    await session.flush()
    e3 = await logger.record(m.id, "test", m.id, "third")
    await session.flush()

    assert e1.sequence == 1
    assert e2.sequence == 2
    assert e3.sequence == 3


@pytest.mark.asyncio
async def test_get_events(session: AsyncSession):
    m = Manuscript(title="Get Events Test")
    session.add(m)
    await session.flush()

    logger = EventLogger(session)
    for i in range(5):
        await logger.record(m.id, "scene", uuid.uuid4(), f"event_{i}")
    await session.flush()

    events = await logger.get_events(m.id, entity_type="scene")
    assert len(events) == 5


@pytest.mark.asyncio
async def test_events_filtered_by_entity(session: AsyncSession):
    m = Manuscript(title="Filter Test")
    session.add(m)
    await session.flush()

    logger = EventLogger(session)
    target_id = uuid.uuid4()
    other_id = uuid.uuid4()

    await logger.record(m.id, "scene", target_id, "create")
    await logger.record(m.id, "scene", other_id, "create")
    await logger.record(m.id, "scene", target_id, "update")
    await session.flush()

    events = await logger.get_events(m.id, entity_type="scene", entity_id=target_id)
    assert len(events) == 2
