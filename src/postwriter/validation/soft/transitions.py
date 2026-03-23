"""Transitions critic: evaluates scene opening, closing, and internal flow."""

from postwriter.validation.base import register_soft_critic
from postwriter.validation.soft.base import BaseSoftCritic, ValidationContext


@register_soft_critic("transitions")
class TransitionsCritic(BaseSoftCritic):
    dimension = "transition_quality"
    system_prompt = (
        "You are a transitions analyst for literary fiction. "
        "Evaluate how the scene opens, closes, and flows internally. "
        "Good scenes enter late and leave early. Openings should orient without "
        "over-explaining. Closings should create forward pull."
    )
    evaluation_prompt_template = (
        "Evaluate transitions and flow:\n"
        "- Does the scene opening orient the reader efficiently?\n"
        "- Does the scene enter at the right moment (not too early with setup)?\n"
        "- Does the closing create forward momentum or resonance?\n"
        "- Do internal transitions between beats flow naturally?\n"
        "- Are there awkward jumps or draggy connective tissue?\n"
        "Score 0.0 = clumsy openings/closings, disjointed flow. 1.0 = seamless, purposeful movement."
    )

    def _extra_context(self, ctx: ValidationContext) -> str:
        parts = []
        if ctx.preceding_scenes:
            last = ctx.preceding_scenes[-1]
            prose = last.get("accepted_prose", "")
            if prose:
                parts.append(f"\n## Previous Scene Ending\n...{prose[-300:]}")
        return "\n".join(parts)
