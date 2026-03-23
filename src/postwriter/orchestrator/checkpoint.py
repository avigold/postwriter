"""Checkpoint and resume: saves orchestrator state to Redis for crash recovery."""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from typing import Any

import redis.asyncio as redis

from postwriter.config import RedisSettings

logger = logging.getLogger(__name__)


@dataclass
class CheckpointData:
    """Serializable orchestrator state for resume."""

    manuscript_id: str
    phase: str  # "planning", "drafting", "revising", "complete"
    current_chapter_ordinal: int = 0
    current_scene_ordinal: int = 0
    total_words: int = 0
    scenes_processed: int = 0
    token_usage: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "manuscript_id": self.manuscript_id,
            "phase": self.phase,
            "current_chapter_ordinal": self.current_chapter_ordinal,
            "current_scene_ordinal": self.current_scene_ordinal,
            "total_words": self.total_words,
            "scenes_processed": self.scenes_processed,
            "token_usage": self.token_usage,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CheckpointData:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class CheckpointManager:
    """Manages session checkpoints in Redis."""

    KEY_PREFIX = "postwriter:checkpoint:"

    def __init__(self, settings: RedisSettings | None = None) -> None:
        self._settings = settings or RedisSettings()
        self._client: redis.Redis | None = None

    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(self._settings.url)
        return self._client

    def _key(self, manuscript_id: str) -> str:
        return f"{self.KEY_PREFIX}{manuscript_id}"

    async def save(self, checkpoint: CheckpointData) -> None:
        """Save a checkpoint."""
        try:
            client = await self._get_client()
            await client.set(
                self._key(checkpoint.manuscript_id),
                json.dumps(checkpoint.to_dict()),
                ex=86400 * 7,  # 7 day TTL
            )
        except Exception as e:
            logger.warning("Failed to save checkpoint: %s", e)

    async def load(self, manuscript_id: str) -> CheckpointData | None:
        """Load a checkpoint if one exists."""
        try:
            client = await self._get_client()
            data = await client.get(self._key(manuscript_id))
            if data:
                return CheckpointData.from_dict(json.loads(data))
        except Exception as e:
            logger.warning("Failed to load checkpoint: %s", e)
        return None

    async def delete(self, manuscript_id: str) -> None:
        """Delete a checkpoint after successful completion."""
        try:
            client = await self._get_client()
            await client.delete(self._key(manuscript_id))
        except Exception as e:
            logger.warning("Failed to delete checkpoint: %s", e)

    async def list_incomplete(self) -> list[CheckpointData]:
        """List all incomplete session checkpoints."""
        try:
            client = await self._get_client()
            keys = []
            async for key in client.scan_iter(f"{self.KEY_PREFIX}*"):
                keys.append(key)

            checkpoints = []
            for key in keys:
                data = await client.get(key)
                if data:
                    cp = CheckpointData.from_dict(json.loads(data))
                    if cp.phase != "complete":
                        checkpoints.append(cp)
            return checkpoints
        except Exception as e:
            logger.warning("Failed to list checkpoints: %s", e)
            return []

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
