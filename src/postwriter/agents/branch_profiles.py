"""Branch profiles: named stylistic variations for multi-branch scene drafting.

Each profile modifies the base style profile in a specific direction,
producing drafts that differ in rhetorical mode rather than being random paraphrases.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BranchProfile:
    """A named stylistic variation applied on top of the base style profile."""

    label: str
    description: str
    modifiers: dict[str, Any]
    writing_instructions: str


# Pre-defined branch profiles
BRANCH_PROFILES: dict[str, BranchProfile] = {
    "restrained_subtext_heavy": BranchProfile(
        label="restrained_subtext_heavy",
        description="Maximum restraint. Meaning lives beneath the surface. Characters say less than they mean.",
        modifiers={
            "directness": -0.3,
            "subtext_target": +0.3,
            "lyricism_target": -0.1,
        },
        writing_instructions=(
            "Write with maximum restraint. Characters should communicate through what they "
            "choose NOT to say. Prefer silence beats, evasive replies, and loaded object references. "
            "Avoid direct emotional statement. Let the reader infer from behavior and detail selection."
        ),
    ),
    "lyrical_image_forward": BranchProfile(
        label="lyrical_image_forward",
        description="Heightened imagery and rhythmic prose. Meaning carried through figurative language.",
        modifiers={
            "lyricism_target": +0.3,
            "metaphor_density": +0.2,
            "directness": -0.1,
        },
        writing_instructions=(
            "Write with heightened attention to imagery and prose rhythm. Use metaphor, simile, "
            "and sensory detail as primary meaning-carriers. Vary sentence length deliberately. "
            "Allow periodic sentences and cumulative constructions. Don't sacrifice clarity for beauty."
        ),
    ),
    "sparse_pressure_through_silence": BranchProfile(
        label="sparse_pressure_through_silence",
        description="Stripped-back prose. Short sentences. Tension through what's withheld.",
        modifiers={
            "directness": +0.1,
            "lyricism_target": -0.3,
            "fragment_tolerance": +0.3,
        },
        writing_instructions=(
            "Write spare, compressed prose. Short sentences. Sentence fragments where they add pressure. "
            "Minimal figurative language. Tension comes from pacing and absence, not description. "
            "Dialogue should be clipped. Avoid explaining emotions."
        ),
    ),
    "formal_cold_surface": BranchProfile(
        label="formal_cold_surface",
        description="Controlled, formal register. Emotional distance. Precision over warmth.",
        modifiers={
            "directness": +0.2,
            "irony_target": +0.2,
            "lyricism_target": -0.2,
        },
        writing_instructions=(
            "Write with a controlled, somewhat formal register. Maintain emotional distance. "
            "Prefer precise nouns and verbs over modifiers. Use ironic undertone where appropriate. "
            "The narrator observes rather than empathizes. Periodic syntax is acceptable."
        ),
    ),
    "intimate_free_indirect": BranchProfile(
        label="intimate_free_indirect",
        description="Close psychic distance. Free indirect discourse. The narrator bleeds into the character.",
        modifiers={
            "subtext_target": +0.1,
            "directness": -0.1,
        },
        writing_instructions=(
            "Write in close free indirect discourse. The narrator's voice should blur with the "
            "POV character's thoughts. Use the character's vocabulary and sentence rhythms in narration. "
            "Interior life surfaces through diction choices, not explicit thought tags. "
            "The reader should feel inside the character's head without 'she thought' markers."
        ),
    ),
    "aggressively_compressed": BranchProfile(
        label="aggressively_compressed",
        description="Maximum compression. Every sentence earns its place. Cut everything non-essential.",
        modifiers={
            "directness": +0.2,
            "lyricism_target": -0.2,
            "exposition_tolerance": -0.3,
        },
        writing_instructions=(
            "Write with aggressive compression. Every sentence must justify its existence. "
            "Cut all filler, throat-clearing, and scenic padding. Enter scenes late, leave early. "
            "Dialogue should do double duty (reveal character AND advance plot). "
            "Prefer action and dialogue over narration."
        ),
    ),
    "scenic_expansion_high_tension": BranchProfile(
        label="scenic_expansion_high_tension",
        description="Expanded scenic detail with sustained tension. Time slows. Details accumulate pressure.",
        modifiers={
            "lyricism_target": +0.1,
            "exposition_tolerance": +0.2,
        },
        writing_instructions=(
            "Write with expanded scenic detail. Slow time down. Let small observations accumulate "
            "into tension. Describe physical environment and body language in precise detail. "
            "The reader should feel the scene unfolding in near-real-time. "
            "Use detail selection to create unease rather than explicit tension statements."
        ),
    ),
}

DEFAULT_BRANCH_LABELS = [
    "restrained_subtext_heavy",
    "lyrical_image_forward",
    "sparse_pressure_through_silence",
]

PIVOTAL_BRANCH_LABELS = [
    "restrained_subtext_heavy",
    "lyrical_image_forward",
    "sparse_pressure_through_silence",
    "intimate_free_indirect",
    "scenic_expansion_high_tension",
]


def get_branch_profiles(
    count: int = 3,
    is_pivotal: bool = False,
    exclude: list[str] | None = None,
) -> list[BranchProfile]:
    """Select branch profiles for scene drafting."""
    exclude = exclude or []
    labels = PIVOTAL_BRANCH_LABELS if is_pivotal else DEFAULT_BRANCH_LABELS

    profiles = [
        BRANCH_PROFILES[label]
        for label in labels
        if label not in exclude and label in BRANCH_PROFILES
    ]
    return profiles[:count]


def apply_profile_modifiers(
    base_style: dict[str, Any],
    profile: BranchProfile,
) -> dict[str, Any]:
    """Apply a branch profile's modifiers to a base style profile dict."""
    modified = dict(base_style)
    for key, delta in profile.modifiers.items():
        if key in modified and isinstance(modified[key], (int, float)):
            modified[key] = max(0.0, min(1.0, modified[key] + delta))
    return modified
