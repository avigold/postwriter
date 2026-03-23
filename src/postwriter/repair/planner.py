"""Repair planner: merges validation results into ordered repair actions."""

from __future__ import annotations

from postwriter.repair.actions import RepairActionSpec
from postwriter.types import RepairPriority, ValidationResult


class RepairPlanner:
    """Converts validation results into an ordered list of repair actions.

    Priority ordering follows Section 12.2:
    1. Hard legality
    2. Canon continuity
    3. Knowledge state
    4. Setup/payoff
    5. Dramatic clarity
    6. Emotional credibility
    7. Voice drift
    8. Device overuse
    9. Rhythmic stagnation
    10. Optional enrichment
    """

    # Map validator names to repair priorities
    PRIORITY_MAP: dict[str, RepairPriority] = {
        "banned_patterns": RepairPriority.HARD_LEGALITY,
        "continuity": RepairPriority.CANON_CONTINUITY,
        "pov": RepairPriority.HARD_LEGALITY,
        "timeline": RepairPriority.CANON_CONTINUITY,
        "knowledge_state": RepairPriority.KNOWLEDGE_STATE,
        "setup_payoff": RepairPriority.SETUP_PAYOFF,
        # Soft critics (to be added in Phase 4)
        "tension": RepairPriority.DRAMATIC_CLARITY,
        "emotion": RepairPriority.EMOTIONAL_CREDIBILITY,
        "voice_consistency": RepairPriority.VOICE_DRIFT,
        "prose_vitality": RepairPriority.OPTIONAL_ENRICHMENT,
        "dialogue": RepairPriority.DRAMATIC_CLARITY,
        "redundancy": RepairPriority.OPTIONAL_ENRICHMENT,
    }

    def plan(self, results: list[ValidationResult]) -> list[RepairActionSpec]:
        """Convert validation failures into ordered repair actions."""
        actions: list[RepairActionSpec] = []

        for result in results:
            if self._needs_repair(result):
                action = self._result_to_action(result)
                if action:
                    actions.append(action)

        # Sort by priority (lower number = higher priority)
        actions.sort(key=lambda a: a.priority.value)
        return actions

    def _needs_repair(self, result: ValidationResult) -> bool:
        """Determine if a validation result requires repair."""
        if result.is_hard:
            return result.passed is False
        # Soft critic: repair if score is below threshold
        if result.score is not None and result.score < 0.4:
            return True
        return False

    def _result_to_action(self, result: ValidationResult) -> RepairActionSpec | None:
        priority = self.PRIORITY_MAP.get(
            result.validator_name, RepairPriority.OPTIONAL_ENRICHMENT
        )

        if result.validator_name == "banned_patterns":
            return self._banned_pattern_action(result, priority)
        elif result.validator_name == "continuity":
            return self._continuity_action(result, priority)
        elif result.validator_name == "pov":
            return self._pov_action(result, priority)
        elif result.validator_name == "timeline":
            return self._timeline_action(result, priority)
        elif result.validator_name == "knowledge_state":
            return self._knowledge_action(result, priority)
        else:
            return self._generic_action(result, priority)

    def _banned_pattern_action(
        self, result: ValidationResult, priority: RepairPriority
    ) -> RepairActionSpec:
        phrases = [e.get("phrase", "") for e in result.evidence[:5]]
        return RepairActionSpec(
            priority=priority,
            target_dimension="banned_patterns",
            instruction=(
                f"Remove or rephrase the following banned phrases/patterns: {', '.join(phrases)}. "
                "Replace with fresh, original phrasing that serves the same function. "
                "Do not simply delete — find a better way to express the same meaning."
            ),
            preserve_constraints=["emotional_force", "scene_purpose", "voice"],
            issue_diagnosis=result.diagnosis,
            issue_evidence=result.evidence,
        )

    def _continuity_action(
        self, result: ValidationResult, priority: RepairPriority
    ) -> RepairActionSpec:
        return RepairActionSpec(
            priority=priority,
            target_dimension="continuity",
            instruction=(
                f"Fix continuity issues: {result.diagnosis}. "
                "Correct character presence, location, or state contradictions. "
                "Make minimal changes to resolve the inconsistency."
            ),
            preserve_constraints=["emotional_arc", "scene_purpose", "prose_quality"],
            issue_diagnosis=result.diagnosis,
            issue_evidence=result.evidence,
        )

    def _pov_action(
        self, result: ValidationResult, priority: RepairPriority
    ) -> RepairActionSpec:
        return RepairActionSpec(
            priority=priority,
            target_dimension="pov",
            instruction=(
                f"Fix POV violations: {result.diagnosis}. "
                "Remove or externalize any narration of non-POV characters' internal states. "
                "Show their emotions through observable behavior, dialogue, and body language instead."
            ),
            preserve_constraints=["scene_purpose", "emotional_force"],
            banned_interventions=["switching_pov", "adding_thought_tags_to_non_pov"],
            issue_diagnosis=result.diagnosis,
            issue_evidence=result.evidence,
        )

    def _timeline_action(
        self, result: ValidationResult, priority: RepairPriority
    ) -> RepairActionSpec:
        return RepairActionSpec(
            priority=priority,
            target_dimension="timeline",
            instruction=(
                f"Fix timeline issues: {result.diagnosis}. "
                "Correct temporal references to be consistent with the scene's time marker "
                "and preceding scenes."
            ),
            preserve_constraints=["scene_purpose", "emotional_arc"],
            issue_diagnosis=result.diagnosis,
            issue_evidence=result.evidence,
        )

    def _knowledge_action(
        self, result: ValidationResult, priority: RepairPriority
    ) -> RepairActionSpec:
        return RepairActionSpec(
            priority=priority,
            target_dimension="knowledge_state",
            instruction=(
                f"Fix knowledge state violations: {result.diagnosis}. "
                "Remove or modify passages where characters act on information they shouldn't have. "
                "Characters can make reasonable inferences but should not know unlearned facts."
            ),
            preserve_constraints=["scene_purpose", "dramatic_tension"],
            issue_diagnosis=result.diagnosis,
            issue_evidence=result.evidence,
        )

    def _generic_action(
        self, result: ValidationResult, priority: RepairPriority
    ) -> RepairActionSpec:
        return RepairActionSpec(
            priority=priority,
            target_dimension=result.validator_name,
            instruction=(
                f"Address {result.validator_name} issue: {result.diagnosis}. "
                "Make targeted improvements while preserving what works."
            ),
            preserve_constraints=["scene_purpose", "voice", "continuity"],
            issue_diagnosis=result.diagnosis,
            issue_evidence=result.evidence,
        )
