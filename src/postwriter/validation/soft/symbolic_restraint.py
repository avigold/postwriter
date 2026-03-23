"""Symbolic restraint critic: evaluates whether symbols are used with appropriate subtlety."""

from postwriter.validation.base import register_soft_critic
from postwriter.validation.soft.base import BaseSoftCritic, ValidationContext


@register_soft_critic("symbolic_restraint")
class SymbolicRestraintCritic(BaseSoftCritic):
    dimension = "symbolic_restraint"
    system_prompt = (
        "You are a symbolic analysis expert for literary fiction. "
        "Evaluate whether symbolic and metaphorical elements are handled with restraint. "
        "Good symbolism is felt before it's understood. Overloaded symbolism becomes allegory. "
        "The best symbols work as literal story elements that accrue additional meaning."
    )
    evaluation_prompt_template = (
        "Evaluate symbolic restraint:\n"
        "- Are symbols present but understated, or are they heavy-handed?\n"
        "- Does the narrator draw attention to symbolic significance (bad) or let it emerge (good)?\n"
        "- Is there symbol pileup — too many loaded images competing for attention?\n"
        "- Do symbolic elements function as real objects/events in the story, not just as signifiers?\n"
        "Score 0.0 = heavy-handed symbolism, allegory, or symbol inflation. "
        "1.0 = symbols are present with perfect restraint, felt rather than announced."
    )

    def _extra_context(self, ctx: ValidationContext) -> str:
        symbols = ctx.scene_brief.get("symbols_touched", [])
        if symbols:
            return f"\n## Symbols This Scene May Touch\n{', '.join(symbols)}"
        return ""
