"""Core enums, type aliases, and protocols for the postwriter system."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ModelTier(str, enum.Enum):
    """LLM model tier for cost/quality routing."""

    OPUS = "opus"
    SONNET = "sonnet"
    HAIKU = "haiku"


class ManuscriptStatus(str, enum.Enum):
    BOOTSTRAPPING = "bootstrapping"
    PLANNING = "planning"
    DRAFTING = "drafting"
    REVISING = "revising"
    COMPLETE = "complete"


class SceneStatus(str, enum.Enum):
    PENDING = "pending"
    DRAFTING = "drafting"
    VALIDATING = "validating"
    REPAIRING = "repairing"
    ACCEPTED = "accepted"


class BranchStatus(str, enum.Enum):
    ACTIVE = "active"
    SELECTED = "selected"
    PRUNED = "pruned"


class PromiseStatus(str, enum.Enum):
    OPEN = "open"
    MATURING = "maturing"
    RESOLVED = "resolved"
    ABANDONED = "abandoned"
    OVERDUE = "overdue"


class PromiseType(str, enum.Enum):
    PLOT = "plot"
    EMOTIONAL = "emotional"
    THEMATIC = "thematic"
    SYMBOLIC = "symbolic"
    TONAL = "tonal"
    RHETORICAL = "rhetorical"


class DependencyType(str, enum.Enum):
    SETUP = "setup"
    PAYOFF = "payoff"
    CONTINUITY = "continuity"
    THEMATIC = "thematic"
    SYMBOLIC = "symbolic"
    CAUSAL = "causal"


class PromiseLinkType(str, enum.Enum):
    INTRODUCES = "introduces"
    DEVELOPS = "develops"
    RESOLVES = "resolves"


class EventParticipantRole(str, enum.Enum):
    PARTICIPANT = "participant"
    WITNESS = "witness"
    INFORMED = "informed"


class RepairPriority(int, enum.Enum):
    """Lower number = higher priority."""

    HARD_LEGALITY = 1
    CANON_CONTINUITY = 2
    KNOWLEDGE_STATE = 3
    SETUP_PAYOFF = 4
    DRAMATIC_CLARITY = 5
    EMOTIONAL_CREDIBILITY = 6
    VOICE_DRIFT = 7
    DEVICE_OVERUSE = 8
    RHYTHMIC_STAGNATION = 9
    OPTIONAL_ENRICHMENT = 10


class RepairStatus(str, enum.Enum):
    PLANNED = "planned"
    APPLIED = "applied"
    VERIFIED = "verified"
    REVERTED = "reverted"


class DeviceCategory(str, enum.Enum):
    LEXICAL_SYNTACTIC = "lexical_syntactic"
    FIGURATIVE = "figurative"
    NARRATIVE_DISCOURSE = "narrative_discourse"
    RHYTHM_PROSE_MOTION = "rhythm_prose_motion"


class DeviceType(str, enum.Enum):
    # Lexical / syntactic
    ALLITERATION = "alliteration"
    ASSONANCE = "assonance"
    ANAPHORA = "anaphora"
    EPISTROPHE = "epistrophe"
    POLYPTOTON = "polyptoton"
    PARALLELISM = "parallelism"
    RHETORICAL_QUESTION = "rhetorical_question"
    TRIADIC_CONSTRUCTION = "triadic_construction"
    SENTENCE_FRAGMENT = "sentence_fragment"
    PERIODIC_SENTENCE = "periodic_sentence"
    CUMULATIVE_SENTENCE = "cumulative_sentence"
    INVERSION = "inversion"
    PARATAXIS = "parataxis"
    HYPOTAXIS = "hypotaxis"
    POLYSYNDETON = "polysyndeton"
    ASYNDETON = "asyndeton"
    DELIBERATE_LEXICAL_RECURRENCE = "deliberate_lexical_recurrence"

    # Figurative
    METAPHOR = "metaphor"
    SIMILE = "simile"
    METONYMY = "metonymy"
    SYNECDOCHE = "synecdoche"
    PERSONIFICATION = "personification"
    HYPERBOLE = "hyperbole"
    UNDERSTATEMENT = "understatement"
    IRONY = "irony"
    PARADOX = "paradox"
    SYMBOL_RECURRENCE = "symbol_recurrence"
    MOTIF_RECURRENCE = "motif_recurrence"
    OBJECTIVE_CORRELATIVE = "objective_correlative"

    # Narrative / discourse
    FORESHADOWING = "foreshadowing"
    CALLBACK = "callback"
    ECHO = "echo"
    DELAYED_REVELATION = "delayed_revelation"
    WITHHELD_INFORMATION = "withheld_information"
    FREE_INDIRECT_DISCOURSE = "free_indirect_discourse"
    INTERIOR_MONOLOGUE = "interior_monologue"
    EXPOSITION_BLOCK = "exposition_block"
    SCENIC_EXPANSION = "scenic_expansion"
    SUMMARY_COMPRESSION = "summary_compression"
    TONAL_PIVOT = "tonal_pivot"
    MISDIRECTION = "misdirection"
    RECOGNITION_BEAT = "recognition_beat"
    REVERSAL_BEAT = "reversal_beat"
    SILENCE_BEAT = "silence_beat"
    EVASIVE_REPLY = "evasive_reply"
    LOADED_OBJECT_REFERENCE = "loaded_object_reference"
    SUBTEXT_EXCHANGE = "subtext_exchange"

    # Rhythm and prose-motion
    LONG_PERIODIC_BUILD = "long_periodic_build"
    CLIPPED_ACCELERATION = "clipped_acceleration"
    DIALOGUE_VOLLEY = "dialogue_volley"
    PARAGRAPH_CONTRACTION = "paragraph_contraction"
    PARAGRAPH_DILATION = "paragraph_dilation"
    RHYTHMIC_ECHO = "rhythmic_echo"
    SYNTAX_PRESSURE_CLUSTER = "syntax_pressure_cluster"


# Map device types to their categories
DEVICE_CATEGORY_MAP: dict[DeviceType, DeviceCategory] = {}
_LEXICAL = [
    DeviceType.ALLITERATION, DeviceType.ASSONANCE, DeviceType.ANAPHORA,
    DeviceType.EPISTROPHE, DeviceType.POLYPTOTON, DeviceType.PARALLELISM,
    DeviceType.RHETORICAL_QUESTION, DeviceType.TRIADIC_CONSTRUCTION,
    DeviceType.SENTENCE_FRAGMENT, DeviceType.PERIODIC_SENTENCE,
    DeviceType.CUMULATIVE_SENTENCE, DeviceType.INVERSION, DeviceType.PARATAXIS,
    DeviceType.HYPOTAXIS, DeviceType.POLYSYNDETON, DeviceType.ASYNDETON,
    DeviceType.DELIBERATE_LEXICAL_RECURRENCE,
]
_FIGURATIVE = [
    DeviceType.METAPHOR, DeviceType.SIMILE, DeviceType.METONYMY,
    DeviceType.SYNECDOCHE, DeviceType.PERSONIFICATION, DeviceType.HYPERBOLE,
    DeviceType.UNDERSTATEMENT, DeviceType.IRONY, DeviceType.PARADOX,
    DeviceType.SYMBOL_RECURRENCE, DeviceType.MOTIF_RECURRENCE,
    DeviceType.OBJECTIVE_CORRELATIVE,
]
_NARRATIVE = [
    DeviceType.FORESHADOWING, DeviceType.CALLBACK, DeviceType.ECHO,
    DeviceType.DELAYED_REVELATION, DeviceType.WITHHELD_INFORMATION,
    DeviceType.FREE_INDIRECT_DISCOURSE, DeviceType.INTERIOR_MONOLOGUE,
    DeviceType.EXPOSITION_BLOCK, DeviceType.SCENIC_EXPANSION,
    DeviceType.SUMMARY_COMPRESSION, DeviceType.TONAL_PIVOT,
    DeviceType.MISDIRECTION, DeviceType.RECOGNITION_BEAT,
    DeviceType.REVERSAL_BEAT, DeviceType.SILENCE_BEAT,
    DeviceType.EVASIVE_REPLY, DeviceType.LOADED_OBJECT_REFERENCE,
    DeviceType.SUBTEXT_EXCHANGE,
]
_RHYTHM = [
    DeviceType.LONG_PERIODIC_BUILD, DeviceType.CLIPPED_ACCELERATION,
    DeviceType.DIALOGUE_VOLLEY, DeviceType.PARAGRAPH_CONTRACTION,
    DeviceType.PARAGRAPH_DILATION, DeviceType.RHYTHMIC_ECHO,
    DeviceType.SYNTAX_PRESSURE_CLUSTER,
]
for _dt in _LEXICAL:
    DEVICE_CATEGORY_MAP[_dt] = DeviceCategory.LEXICAL_SYNTACTIC
for _dt in _FIGURATIVE:
    DEVICE_CATEGORY_MAP[_dt] = DeviceCategory.FIGURATIVE
for _dt in _NARRATIVE:
    DEVICE_CATEGORY_MAP[_dt] = DeviceCategory.NARRATIVE_DISCOURSE
for _dt in _RHYTHM:
    DEVICE_CATEGORY_MAP[_dt] = DeviceCategory.RHYTHM_PROSE_MOTION


class ValidationSeverity(str, enum.Enum):
    HARD = "hard"
    SOFT = "soft"


class PhaseStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Agent protocol and result types
# ---------------------------------------------------------------------------


@dataclass
class AgentContext:
    """Context passed to any agent for execution."""

    manuscript_id: str
    # The canon slicer populates these based on what the agent needs
    premise: str = ""
    controlling_design: dict[str, Any] = field(default_factory=dict)
    style_profile: dict[str, Any] = field(default_factory=dict)
    chapter_brief: dict[str, Any] = field(default_factory=dict)
    scene_brief: dict[str, Any] = field(default_factory=dict)
    characters: list[dict[str, Any]] = field(default_factory=list)
    character_states: list[dict[str, Any]] = field(default_factory=list)
    preceding_scenes: list[dict[str, Any]] = field(default_factory=list)
    open_promises: list[dict[str, Any]] = field(default_factory=list)
    linked_scenes: list[dict[str, Any]] = field(default_factory=list)
    # User-provided context files (from context/ directory)
    user_context: list[dict[str, Any]] = field(default_factory=list)
    user_context_images: list[str] = field(default_factory=list)  # file paths
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Base result from any agent execution."""

    success: bool
    agent_role: str
    model_tier: ModelTier
    input_tokens: int = 0
    output_tokens: int = 0
    raw_response: str = ""
    parsed: Any = None
    error: str | None = None


@runtime_checkable
class Agent(Protocol):
    """Protocol that all agent implementations must follow."""

    role: str
    model_tier: ModelTier

    async def execute(self, context: AgentContext) -> AgentResult: ...


@runtime_checkable
class Validator(Protocol):
    """Protocol for hard validators."""

    name: str

    async def validate(
        self,
        prose: str,
        scene_brief: dict[str, Any],
        canon_slice: dict[str, Any],
    ) -> ValidationResult: ...


@dataclass
class ValidationResult:
    """Result from a hard validator or soft critic."""

    validator_name: str
    is_hard: bool
    passed: bool | None  # None for soft critics
    score: float | None  # None for hard validators
    diagnosis: str = ""
    evidence: list[dict[str, Any]] = field(default_factory=list)
    span_references: list[tuple[int, int]] = field(default_factory=list)
    repair_opportunities: list[str] = field(default_factory=list)
    confidence: float = 1.0
