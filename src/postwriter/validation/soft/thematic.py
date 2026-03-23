"""Thematic critic: evaluates thematic integration without overstatement."""

from postwriter.validation.base import register_soft_critic
from postwriter.validation.soft.base import BaseSoftCritic, ValidationContext


@register_soft_critic("thematic")
class ThematicCritic(BaseSoftCritic):
    dimension = "thematic_integration"
    system_prompt = (
        "You are a thematic analyst for literary fiction. "
        "Evaluate whether the scene engages its themes through dramatization rather than "
        "statement. Themes should be embodied in character action, situation, and detail — "
        "never in narrator editorializing."
    )
    evaluation_prompt_template = (
        "Evaluate thematic integration:\n"
        "- Are the themes listed in the brief present in the scene?\n"
        "- Are they embodied through action, detail, and situation — or stated by the narrator?\n"
        "- Is there thematic overstatement (hitting the reader over the head)?\n"
        "- Does the scene add thematic texture without being preachy?\n"
        "Score 0.0 = themes absent or crudely stated. 1.0 = themes alive in the scene's fabric without being named."
    )

    def _extra_context(self, ctx: ValidationContext) -> str:
        themes = ctx.scene_brief.get("themes_touched", [])
        if themes:
            return f"\n## Themes This Scene Should Touch\n{', '.join(themes)}"
        return ""
