"""Custom exception hierarchy for the postwriter system."""


class PostwriterError(Exception):
    """Base exception for all postwriter errors."""


class CanonViolation(PostwriterError):
    """A hard canon constraint was violated."""

    def __init__(self, entity_type: str, entity_id: str, message: str) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"Canon violation on {entity_type}[{entity_id}]: {message}")


class ValidationError(PostwriterError):
    """A hard validation check failed."""

    def __init__(self, validator_name: str, message: str) -> None:
        self.validator_name = validator_name
        super().__init__(f"Validation failed [{validator_name}]: {message}")


class BudgetExhausted(PostwriterError):
    """Token budget for a model tier has been exhausted."""

    def __init__(self, tier: str, used: int, limit: int) -> None:
        self.tier = tier
        self.used = used
        self.limit = limit
        super().__init__(f"Token budget exhausted for {tier}: {used}/{limit}")


class OrchestratorStop(PostwriterError):
    """The orchestrator has hit a stop condition."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Orchestrator stopped: {reason}")


class RepairDivergence(PostwriterError):
    """The repair loop failed to converge."""

    def __init__(self, scene_id: str, rounds: int) -> None:
        self.scene_id = scene_id
        self.rounds = rounds
        super().__init__(
            f"Repair loop diverged for scene {scene_id} after {rounds} rounds"
        )


class LLMError(PostwriterError):
    """An LLM call failed after retries."""

    def __init__(self, tier: str, message: str) -> None:
        self.tier = tier
        super().__init__(f"LLM error [{tier}]: {message}")


class ParseError(PostwriterError):
    """Failed to parse structured output from an LLM response."""

    def __init__(self, agent_role: str, message: str) -> None:
        self.agent_role = agent_role
        super().__init__(f"Parse error from {agent_role}: {message}")
