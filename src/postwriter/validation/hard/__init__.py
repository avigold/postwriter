"""Hard validators: pass/fail checks that block scene acceptance."""

# Import all validators to trigger registration
from postwriter.validation.hard.banned_patterns import BannedPatternsValidator
from postwriter.validation.hard.continuity import ContinuityValidator
from postwriter.validation.hard.knowledge import KnowledgeStateValidator
from postwriter.validation.hard.pov import POVValidator
from postwriter.validation.hard.timeline import TimelineValidator

__all__ = [
    "BannedPatternsValidator",
    "ContinuityValidator",
    "KnowledgeStateValidator",
    "POVValidator",
    "TimelineValidator",
]
