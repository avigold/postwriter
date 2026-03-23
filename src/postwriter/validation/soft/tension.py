"""Tension critic: evaluates dramatic tension and forward momentum."""

from postwriter.validation.base import register_soft_critic
from postwriter.validation.soft.base import BaseSoftCritic


@register_soft_critic("tension")
class TensionCritic(BaseSoftCritic):
    dimension = "tension"
    system_prompt = (
        "You are a dramatic tension analyst for literary fiction. "
        "Evaluate whether a scene creates, sustains, and modulates tension effectively. "
        "Low tension is not always bad — some scenes should release pressure — but the "
        "tension should serve the scene's dramatic function."
    )
    evaluation_prompt_template = (
        "Evaluate the dramatic tension in this scene:\n"
        "- Does the scene create a sense of stakes and forward momentum?\n"
        "- Does tension build, sustain, or release appropriately for the scene's function?\n"
        "- Are there dead spots where tension collapses without purpose?\n"
        "- Does the conflict feel real, or merely described?\n"
        "Score 0.0 = no tension, inert scene. 1.0 = masterful tension management."
    )
