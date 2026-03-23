"""Model-based detectors for figurative devices (metaphor, simile, irony, etc.)."""

from __future__ import annotations

import json
import logging
from typing import Any

from postwriter.devices.taxonomy import DeviceInstance
from postwriter.llm.client import LLMClient
from postwriter.types import DeviceType, ModelTier

logger = logging.getLogger(__name__)

# Map from response labels to DeviceType
_FIGURATIVE_MAP: dict[str, DeviceType] = {
    "metaphor": DeviceType.METAPHOR,
    "simile": DeviceType.SIMILE,
    "metonymy": DeviceType.METONYMY,
    "synecdoche": DeviceType.SYNECDOCHE,
    "personification": DeviceType.PERSONIFICATION,
    "hyperbole": DeviceType.HYPERBOLE,
    "understatement": DeviceType.UNDERSTATEMENT,
    "irony": DeviceType.IRONY,
    "paradox": DeviceType.PARADOX,
}


class FigurativeDetector:
    """Detects figurative devices using Haiku/Sonnet."""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    async def detect(self, prose: str) -> list[DeviceInstance]:
        prompt = (
            f"## Prose\n{prose[:3000]}\n\n"
            "Identify all figurative language devices in this prose. For each, provide:\n"
            "- type: metaphor, simile, metonymy, synecdoche, personification, hyperbole, "
            "understatement, irony, paradox\n"
            "- quote: the exact text\n"
            "- function: what dramatic/emotional purpose it serves\n"
            "- imagery_domain: the source domain (e.g., 'water', 'architecture', 'body')\n"
            "- intensity: 0.0-1.0\n\n"
            "Respond with JSON: [{type, quote, function, imagery_domain, intensity}]"
        )

        try:
            response = await self._llm.complete(
                tier=ModelTier.HAIKU,
                messages=[{"role": "user", "content": prompt}],
                system="Identify figurative language devices precisely. Only include clear instances.",
                max_tokens=2048,
                temperature=0.0,
            )
            return self._parse(response.text, prose)
        except Exception as e:
            logger.warning("Figurative detection failed: %s", e)
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
            dtype = _FIGURATIVE_MAP.get(item.get("type", "").lower())
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
                imagery_domain=item.get("imagery_domain"),
                intensity=float(item.get("intensity", 0.5)),
                confidence=0.7,
            ))
        return instances
