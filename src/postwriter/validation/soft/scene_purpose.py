"""Scene purpose critic: evaluates whether the scene achieves its stated dramatic purpose."""

from postwriter.validation.base import register_soft_critic
from postwriter.validation.soft.base import BaseSoftCritic


@register_soft_critic("scene_purpose")
class ScenePurposeCritic(BaseSoftCritic):
    dimension = "tension"  # Maps to tension as the closest dimension
    system_prompt = (
        "You are a scene purpose analyst for literary fiction. "
        "Evaluate whether the scene actually accomplishes what it was designed to accomplish. "
        "A scene can be beautifully written but fail its purpose."
    )
    evaluation_prompt_template = (
        "Evaluate whether this scene achieves its stated purpose:\n"
        "- Does the scene fulfill its dramatic function?\n"
        "- Does the specified conflict actually manifest in the prose?\n"
        "- Does the emotional turn happen?\n"
        "- If there's a revelation, is it delivered effectively?\n"
        "- Would removing this scene leave a gap in the story, or is it skippable?\n"
        "Score 0.0 = scene fails its purpose entirely. 1.0 = scene accomplishes exactly what it needs to."
    )
