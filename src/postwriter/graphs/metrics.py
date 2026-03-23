"""Device metrics: density, burstiness, concentration, novelty, clumping."""

from __future__ import annotations

import math
import statistics
from collections import Counter
from dataclasses import dataclass, field

from postwriter.devices.taxonomy import DeviceInstance
from postwriter.types import DeviceType


@dataclass
class DeviceMetrics:
    """Computed metrics for device ecology across a scope (scene, chapter, manuscript)."""

    total_instances: int = 0
    total_words: int = 0
    density_per_1000: float = 0.0

    # Per-type counts
    type_counts: dict[str, int] = field(default_factory=dict)

    # Burstiness: std/mean of inter-occurrence gaps (higher = more bursty)
    burstiness: dict[str, float] = field(default_factory=dict)

    # Functional diversity: how many different functions devices serve
    functional_diversity: float = 0.0

    # Character concentration: fraction of devices attributed to most-common character
    character_concentration: float = 0.0

    # Imagery domain concentration (Herfindahl index)
    imagery_concentration: float = 0.0

    # Novelty mean: average novelty score across instances
    novelty_mean: float = 0.0

    # Local clumping: max device density in any 500-word window
    max_local_density: float = 0.0

    # Same-function same-device count
    same_function_same_device: int = 0


def compute_metrics(
    instances: list[DeviceInstance],
    word_count: int,
) -> DeviceMetrics:
    """Compute all device metrics for a set of instances."""
    m = DeviceMetrics(
        total_instances=len(instances),
        total_words=word_count,
    )

    if not instances or word_count == 0:
        return m

    m.density_per_1000 = len(instances) / word_count * 1000

    # Type counts
    type_counter: Counter[str] = Counter()
    for inst in instances:
        type_counter[inst.device_type.value] += 1
    m.type_counts = dict(type_counter)

    # Burstiness per type (using position-based gaps)
    _compute_burstiness(instances, m)

    # Functional diversity
    functions = {inst.estimated_function for inst in instances if inst.estimated_function}
    m.functional_diversity = len(functions) / max(1, len(instances))

    # Character concentration
    char_counter: Counter[str] = Counter()
    for inst in instances:
        if inst.speaker_character:
            char_counter[inst.speaker_character] += 1
    if char_counter:
        most_common_count = char_counter.most_common(1)[0][1]
        total_with_char = sum(char_counter.values())
        m.character_concentration = most_common_count / total_with_char

    # Imagery concentration
    domain_counter: Counter[str] = Counter()
    for inst in instances:
        if inst.imagery_domain:
            domain_counter[inst.imagery_domain] += 1
    if domain_counter:
        total_domains = sum(domain_counter.values())
        shares = [c / total_domains for c in domain_counter.values()]
        m.imagery_concentration = sum(s * s for s in shares)

    # Novelty mean
    novelty_scores = [inst.novelty_score for inst in instances if inst.novelty_score is not None]
    m.novelty_mean = statistics.mean(novelty_scores) if novelty_scores else 0.0

    # Local clumping (max density in 500-word equivalent windows)
    m.max_local_density = _compute_max_local_density(instances, word_count)

    # Same-function same-device pairs
    m.same_function_same_device = _count_same_function_same_device(instances)

    return m


def _compute_burstiness(instances: list[DeviceInstance], m: DeviceMetrics) -> None:
    """Compute burstiness per device type using position gaps."""
    by_type: dict[str, list[int]] = {}
    for inst in instances:
        by_type.setdefault(inst.device_type.value, []).append(inst.span_start)

    for dtype, positions in by_type.items():
        if len(positions) < 2:
            m.burstiness[dtype] = 0.0
            continue
        positions.sort()
        gaps = [positions[i + 1] - positions[i] for i in range(len(positions) - 1)]
        mean_gap = statistics.mean(gaps)
        std_gap = statistics.stdev(gaps) if len(gaps) > 1 else 0.0
        # Burstiness = (std - mean) / (std + mean), normalized to 0-1
        if std_gap + mean_gap > 0:
            raw = (std_gap - mean_gap) / (std_gap + mean_gap)
            m.burstiness[dtype] = max(0.0, (raw + 1) / 2)  # Normalize to 0-1
        else:
            m.burstiness[dtype] = 0.0


def _compute_max_local_density(
    instances: list[DeviceInstance], word_count: int, window_chars: int = 2500
) -> float:
    """Find the maximum device density in any sliding window."""
    if not instances or word_count == 0:
        return 0.0

    sorted_insts = sorted(instances, key=lambda i: i.span_start)
    max_density = 0.0

    for i, inst in enumerate(sorted_insts):
        window_end = inst.span_start + window_chars
        count = sum(1 for j in sorted_insts[i:] if j.span_start < window_end)
        # Approximate words in window
        approx_words = window_chars / 5  # ~5 chars per word
        density = count / approx_words * 1000
        max_density = max(max_density, density)

    return max_density


def _count_same_function_same_device(instances: list[DeviceInstance]) -> int:
    """Count pairs of adjacent instances with same type AND same function."""
    if len(instances) < 2:
        return 0

    sorted_insts = sorted(instances, key=lambda i: i.span_start)
    count = 0
    for i in range(len(sorted_insts) - 1):
        a, b = sorted_insts[i], sorted_insts[i + 1]
        if (
            a.device_type == b.device_type
            and a.estimated_function
            and a.estimated_function == b.estimated_function
        ):
            count += 1
    return count
