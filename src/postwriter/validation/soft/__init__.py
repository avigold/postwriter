"""Soft critics: scored advisory checks that influence but don't block acceptance."""

from postwriter.validation.soft.dialogue import DialogueCritic
from postwriter.validation.soft.emotion import EmotionCritic
from postwriter.validation.soft.prose_vitality import ProseVitalityCritic
from postwriter.validation.soft.redundancy import RedundancyCritic
from postwriter.validation.soft.scene_purpose import ScenePurposeCritic
from postwriter.validation.soft.symbolic_restraint import SymbolicRestraintCritic
from postwriter.validation.soft.tension import TensionCritic
from postwriter.validation.soft.thematic import ThematicCritic
from postwriter.validation.soft.transitions import TransitionsCritic
from postwriter.validation.soft.voice_consistency import VoiceConsistencyCritic

__all__ = [
    "TensionCritic",
    "EmotionCritic",
    "ProseVitalityCritic",
    "VoiceConsistencyCritic",
    "DialogueCritic",
    "ThematicCritic",
    "RedundancyCritic",
    "TransitionsCritic",
    "ScenePurposeCritic",
    "SymbolicRestraintCritic",
]
