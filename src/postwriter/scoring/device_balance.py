"""Device balance scoring component."""

from __future__ import annotations

from postwriter.devices.overuse_rules import OveruseAlert, detect_overuse
from postwriter.graphs.metrics import DeviceMetrics


def compute_device_balance_score(
    metrics: DeviceMetrics,
    recurrence_caps: dict[str, int] | None = None,
) -> float:
    """Compute a 0-1 device balance score.

    1.0 = well-distributed, varied device usage
    0.0 = severe overuse, clumping, or monoculture
    """
    alerts = detect_overuse(metrics, recurrence_caps)

    if not alerts:
        return 1.0

    # Aggregate severity
    total_severity = sum(a.severity for a in alerts)
    # Normalize: each alert can contribute up to ~0.2 penalty
    penalty = min(1.0, total_severity * 0.2)

    return max(0.0, 1.0 - penalty)
