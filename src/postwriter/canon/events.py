"""Append-only event logger for traceability."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from postwriter.models.events import Event


class EventLogger:
    """Records state mutations as append-only events."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _next_sequence(self, manuscript_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.coalesce(func.max(Event.sequence), 0)).where(
                Event.manuscript_id == manuscript_id
            )
        )
        return result.scalar_one() + 1

    async def record(
        self,
        manuscript_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID,
        event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> Event:
        seq = await self._next_sequence(manuscript_id)
        event = Event(
            manuscript_id=manuscript_id,
            sequence=seq,
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            payload=payload or {},
        )
        self._session.add(event)
        return event

    async def get_events(
        self,
        manuscript_id: uuid.UUID,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        limit: int = 100,
    ) -> list[Event]:
        stmt = select(Event).where(Event.manuscript_id == manuscript_id)
        if entity_type:
            stmt = stmt.where(Event.entity_type == entity_type)
        if entity_id:
            stmt = stmt.where(Event.entity_id == entity_id)
        stmt = stmt.order_by(Event.sequence.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
