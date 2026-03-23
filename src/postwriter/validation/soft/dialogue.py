"""Dialogue critic: evaluates dialogue quality, distinctiveness, and function."""

from postwriter.validation.base import register_soft_critic
from postwriter.validation.soft.base import BaseSoftCritic


@register_soft_critic("dialogue")
class DialogueCritic(BaseSoftCritic):
    dimension = "dialogue_quality"
    system_prompt = (
        "You are a dialogue analyst for literary fiction. "
        "Evaluate whether dialogue sounds like distinct human beings speaking, "
        "whether it serves dramatic function, and whether it avoids common pitfalls "
        "like over-explanation, on-the-nose emotion, and uniform register."
    )
    evaluation_prompt_template = (
        "Evaluate dialogue quality:\n"
        "- Do characters sound distinct from each other?\n"
        "- Does dialogue do double duty (reveal character AND advance plot/tension)?\n"
        "- Is there subtext — characters saying one thing and meaning another?\n"
        "- Does any dialogue explain things characters would already know (As You Know, Bob)?\n"
        "- Are speech patterns consistent with character voice profiles?\n"
        "- Is dialogue attribution varied and unobtrusive?\n"
        "Score 0.0 = indistinguishable voices, expository dialogue. 1.0 = distinctive, layered, functional."
    )
