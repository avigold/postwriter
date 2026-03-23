"""Redundancy critic: evaluates repetition and bloat."""

from postwriter.validation.base import register_soft_critic
from postwriter.validation.soft.base import BaseSoftCritic


@register_soft_critic("redundancy")
class RedundancyCritic(BaseSoftCritic):
    dimension = "redundancy_inverse"
    system_prompt = (
        "You are a redundancy analyst for literary fiction. "
        "Evaluate whether the prose is lean or bloated. Identify repetition of ideas, "
        "images, or phrasings that don't serve a deliberate purpose. "
        "Note: deliberate repetition for emphasis or rhythm is not redundancy."
    )
    evaluation_prompt_template = (
        "Evaluate redundancy (score is INVERSE — higher = less redundant = better):\n"
        "- Are there repeated ideas restated in different words without adding meaning?\n"
        "- Are there unnecessary qualifiers, filler phrases, or throat-clearing?\n"
        "- Could passages be cut without losing meaning or effect?\n"
        "- Is there deliberate repetition that serves a rhetorical purpose (this is acceptable)?\n"
        "- CRITICAL: Does the prose repeat the same rhetorical construction across "
        "multiple sentences or paragraphs? The most common form is the self-referential "
        "observation: 'he noted X in the way he noted Y', 'a thing he had learned to Z', "
        "'the specific quality of A that he had trained himself to B'. If the same "
        "structural formula appears more than twice in a scene, it is a severe "
        "redundancy problem regardless of how varied the content appears. "
        "Score harshly for formulaic repetition of rhetorical structure.\n"
        "Score 0.0 = heavily redundant and bloated. 1.0 = lean, every sentence earns its place."
    )
