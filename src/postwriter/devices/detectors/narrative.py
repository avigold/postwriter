"""Model-based detectors for narrative/discourse devices."""

from __future__ import annotations

import json
import logging
from typing import Any

from postwriter.devices.taxonomy import DeviceInstance
from postwriter.llm.client import LLMClient
from postwriter.types import DeviceType, ModelTier

logger = logging.getLogger(__name__)

_NARRATIVE_MAP: dict[str, DeviceType] = {
    "foreshadowing": DeviceType.FORESHADOWING,
    "callback": DeviceType.CALLBACK,
    "echo": DeviceType.ECHO,
    "delayed_revelation": DeviceType.DELAYED_REVELATION,
    "withheld_information": DeviceType.WITHHELD_INFORMATION,
    "free_indirect_discourse": DeviceType.FREE_INDIRECT_DISCOURSE,
    "interior_monologue": DeviceType.INTERIOR_MONOLOGUE,
    "tonal_pivot": DeviceType.TONAL_PIVOT,
    "misdirection": DeviceType.MISDIRECTION,
    "silence_beat": DeviceType.SILENCE_BEAT,
    "evasive_reply": DeviceType.EVASIVE_REPLY,
    "loaded_object_reference": DeviceType.LOADED_OBJECT_REFERENCE,
    "subtext_exchange": DeviceType.SUBTEXT_EXCHANGE,
}


class NarrativeDetector:
    """Detects narrative and discourse devices using Sonnet."""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    async def detect(
        self,
        prose: str,
        scene_brief: dict[str, Any] | None = None,
    ) -> list[DeviceInstance]:
        context = ""
        if scene_brief:
            context = (
                f"\n## Scene Context\n"
                f"Purpose: {scene_brief.get('purpose', '')}\n"
                f"Conflict: {scene_brief.get('conflict', '')}\n"
            )

        prompt = (
            f"## Prose\n{prose[:3000]}\n{context}\n"
            "Identify narrative/discourse devices in this prose:\n"
            "- foreshadowing, callback, echo, delayed_revelation, withheld_information\n"
            "- free_indirect_discourse, interior_monologue, tonal_pivot, misdirection\n"
            "- silence_beat, evasive_reply, loaded_object_reference, subtext_exchange\n\n"
            "For each: {type, quote, function, confidence (0-1)}\n"
            "Only include instances you're at least moderately confident about.\n"
            "Respond with JSON array."
        )

        try:
            response = await self._llm.complete(
                tier=ModelTier.SONNET,
                messages=[{"role": "user", "content": prompt}],
                system=(
                    "Identify narrative devices precisely. A silence beat is a moment "
                    "where meaningful absence speaks. A subtext exchange is dialogue where "
                    "the real conversation happens beneath the words. Be selective — only "
                    "flag clear instances."
                ),
                max_tokens=2048,
                temperature=0.0,
            )
            return self._parse(response.text, prose)
        except Exception as e:
            logger.warning("Narrative detection failed: %s", e)
            return []

    def _parse(self, text: str, prose: str) -> list[DeviceInstance]:
        text = text.strip()
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:-1])
        try:
            items = json.loads(text)
        except json.JSONDecodeError:
            return []

        instances = []
        for item in items:
            dtype = _NARRATIVE_MAP.get(item.get("type", "").lower())
            if not dtype:
                continue
            quote = item.get("quote", "")
            start = prose.find(quote)
            if start < 0:
                start = 0
            instances.append(DeviceInstance(
                device_type=dtype,
                span_start=start,
                span_end=start + len(quote),
                text=quote[:200],
                estimated_function=item.get("function", ""),
                confidence=float(item.get("confidence", 0.6)),
            ))
        return instances
