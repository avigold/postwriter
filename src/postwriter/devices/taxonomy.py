"""Device taxonomy: instance schema and detection strategy mapping.

DeviceType and DeviceCategory enums live in postwriter.types.
This module adds the instance data class and strategy metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from postwriter.types import DeviceCategory, DeviceType, DEVICE_CATEGORY_MAP


@dataclass
class DeviceInstance:
    """A single detected literary device instance."""

    device_type: DeviceType
    span_start: int  # character offset in prose
    span_end: int
    text: str  # the matched text
    estimated_function: str = ""
    speaker_character: str | None = None
    imagery_domain: str | None = None
    intensity: float = 0.5
    confidence: float = 0.8
    novelty_score: float | None = None
    intentional: bool | None = None
    subtype: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def category(self) -> DeviceCategory:
        return DEVICE_CATEGORY_MAP.get(self.device_type, DeviceCategory.LEXICAL_SYNTACTIC)

    @property
    def word_count(self) -> int:
        return len(self.text.split())


# Which devices can be detected by rule-based methods
RULE_DETECTABLE: set[DeviceType] = {
    DeviceType.ALLITERATION,
    DeviceType.ANAPHORA,
    DeviceType.EPISTROPHE,
    DeviceType.PARALLELISM,
    DeviceType.RHETORICAL_QUESTION,
    DeviceType.TRIADIC_CONSTRUCTION,
    DeviceType.SENTENCE_FRAGMENT,
    DeviceType.POLYSYNDETON,
    DeviceType.ASYNDETON,
    DeviceType.DELIBERATE_LEXICAL_RECURRENCE,
}

# Which devices require model-based detection
MODEL_DETECTABLE: set[DeviceType] = {
    DeviceType.METAPHOR,
    DeviceType.SIMILE,
    DeviceType.METONYMY,
    DeviceType.PERSONIFICATION,
    DeviceType.HYPERBOLE,
    DeviceType.UNDERSTATEMENT,
    DeviceType.IRONY,
    DeviceType.FORESHADOWING,
    DeviceType.CALLBACK,
    DeviceType.FREE_INDIRECT_DISCOURSE,
    DeviceType.SUBTEXT_EXCHANGE,
    DeviceType.SILENCE_BEAT,
    DeviceType.EVASIVE_REPLY,
    DeviceType.LOADED_OBJECT_REFERENCE,
    DeviceType.TONAL_PIVOT,
    DeviceType.MISDIRECTION,
}
