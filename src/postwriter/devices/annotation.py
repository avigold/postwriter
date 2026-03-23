"""Device annotation service: orchestrates all detectors and stores results."""

from __future__ import annotations

import logging
from typing import Any

from postwriter.devices.detectors.lexical import LexicalDetector
from postwriter.devices.detectors.rhythm import RhythmAnalyzer, RhythmProfile
from postwriter.devices.imagery_domains import ImageryDomainClassifier
from postwriter.devices.taxonomy import DeviceInstance
from postwriter.llm.client import LLMClient

logger = logging.getLogger(__name__)


class DeviceAnnotator:
    """Orchestrates rule-based and model-based device detection.

    Runs detectors, deduplicates overlapping instances, classifies imagery
    domains, and returns a complete annotation set.
    """

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm
        self._lexical = LexicalDetector()
        self._rhythm = RhythmAnalyzer()
        self._imagery = ImageryDomainClassifier()

    async def annotate(
        self,
        prose: str,
        scene_brief: dict[str, Any] | None = None,
    ) -> AnnotationResult:
        """Run all detectors and return unified annotations."""
        instances: list[DeviceInstance] = []

        # Rule-based detection (always runs)
        lexical_instances = self._lexical.detect_all(prose)
        instances.extend(lexical_instances)

        # Rhythm analysis (always runs)
        rhythm = self._rhythm.analyze(prose)

        # Model-based detection (if LLM available)
        if self._llm:
            try:
                from postwriter.devices.detectors.figurative import FigurativeDetector
                from postwriter.devices.detectors.narrative import NarrativeDetector

                fig_detector = FigurativeDetector(self._llm)
                nar_detector = NarrativeDetector(self._llm)

                fig_instances = await fig_detector.detect(prose)
                nar_instances = await nar_detector.detect(prose, scene_brief)

                instances.extend(fig_instances)
                instances.extend(nar_instances)
            except Exception as e:
                logger.warning("Model-based detection failed: %s", e)

        # Deduplicate overlapping instances
        instances = self._deduplicate(instances)

        # Classify imagery domains
        self._imagery.classify_all(instances)

        # Build imagery profile
        imagery_profile = self._imagery.profile(instances)

        return AnnotationResult(
            instances=instances,
            rhythm=rhythm,
            imagery_profile=imagery_profile,
            rule_based_count=len(lexical_instances),
            model_based_count=len(instances) - len(lexical_instances),
        )

    def _deduplicate(self, instances: list[DeviceInstance]) -> list[DeviceInstance]:
        """Remove overlapping instances, keeping higher confidence ones."""
        if len(instances) <= 1:
            return instances

        # Sort by span_start, then by confidence (highest first)
        instances.sort(key=lambda i: (i.span_start, -i.confidence))

        deduped: list[DeviceInstance] = []
        for inst in instances:
            # Check if this overlaps significantly with any kept instance
            overlaps = False
            for kept in deduped:
                overlap = _span_overlap(
                    (inst.span_start, inst.span_end),
                    (kept.span_start, kept.span_end),
                )
                # If >50% overlap and same device type, skip
                inst_len = max(1, inst.span_end - inst.span_start)
                if overlap / inst_len > 0.5 and inst.device_type == kept.device_type:
                    overlaps = True
                    break
            if not overlaps:
                deduped.append(inst)

        return deduped


class AnnotationResult:
    """Complete device annotation for a prose passage."""

    __slots__ = (
        "instances", "rhythm", "imagery_profile",
        "rule_based_count", "model_based_count",
    )

    def __init__(
        self,
        instances: list[DeviceInstance],
        rhythm: RhythmProfile,
        imagery_profile: Any,
        rule_based_count: int = 0,
        model_based_count: int = 0,
    ) -> None:
        self.instances = instances
        self.rhythm = rhythm
        self.imagery_profile = imagery_profile
        self.rule_based_count = rule_based_count
        self.model_based_count = model_based_count

    @property
    def total_devices(self) -> int:
        return len(self.instances)

    @property
    def density_per_1000(self) -> float:
        if self.rhythm.word_count == 0:
            return 0.0
        return len(self.instances) / self.rhythm.word_count * 1000

    def by_type(self) -> dict[str, list[DeviceInstance]]:
        result: dict[str, list[DeviceInstance]] = {}
        for inst in self.instances:
            key = inst.device_type.value
            result.setdefault(key, []).append(inst)
        return result


def _span_overlap(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Compute the overlap between two spans."""
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))
