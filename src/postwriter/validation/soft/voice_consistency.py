"""Voice consistency critic: evaluates whether the prose maintains the target voice."""

from postwriter.validation.base import register_soft_critic
from postwriter.validation.soft.base import BaseSoftCritic, ValidationContext


@register_soft_critic("voice_consistency")
class VoiceConsistencyCritic(BaseSoftCritic):
    dimension = "voice_stability"
    system_prompt = (
        "You are a voice consistency analyst for literary fiction. "
        "Evaluate whether the prose maintains a consistent narrative voice that matches "
        "the target style profile. Voice drift — where the narrator suddenly sounds different — "
        "is a common problem in AI-generated fiction."
    )
    evaluation_prompt_template = (
        "Evaluate voice consistency:\n"
        "- Does the prose maintain a consistent register throughout?\n"
        "- Does it match the target voice description?\n"
        "- Are there sudden shifts in diction, formality, or perspective?\n"
        "- Does the narrator's voice remain distinct from character dialogue voices?\n"
        "- Are there passages that sound like a different author wrote them?\n"
        "Score 0.0 = voice is inconsistent or generic. 1.0 = distinctive, stable voice throughout."
    )

    def _extra_context(self, ctx: ValidationContext) -> str:
        parts = []
        sp = ctx.style_profile
        if sp.get("voice_description"):
            parts.append(f"\n## Target Voice\n{sp['voice_description']}")
        if sp.get("directness") is not None:
            parts.append(f"Directness target: {sp['directness']}")
        if sp.get("lyricism_target") is not None:
            parts.append(f"Lyricism target: {sp['lyricism_target']}")
        return "\n".join(parts)
