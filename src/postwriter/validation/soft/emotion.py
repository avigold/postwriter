"""Emotion critic: evaluates emotional credibility and earned feeling."""

from postwriter.validation.base import register_soft_critic
from postwriter.validation.soft.base import BaseSoftCritic


@register_soft_critic("emotion")
class EmotionCritic(BaseSoftCritic):
    dimension = "emotional_credibility"
    system_prompt = (
        "You are an emotional credibility analyst for literary fiction. "
        "Evaluate whether the scene's emotions feel earned, genuine, and proportionate. "
        "Emotions should emerge from situation and character, not from the narrator telling "
        "the reader what to feel."
    )
    evaluation_prompt_template = (
        "Evaluate emotional credibility:\n"
        "- Does the emotional turn described in the brief actually occur in the prose?\n"
        "- Are emotions shown through behavior, detail, and dialogue rather than stated?\n"
        "- Do emotional shifts feel earned by what happens in the scene?\n"
        "- Is there sentimentality, melodrama, or emotional inflation?\n"
        "Score 0.0 = emotionally false/manipulative. 1.0 = fully earned, credible feeling."
    )
