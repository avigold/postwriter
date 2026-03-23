"""Device overuse and underuse detection rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from postwriter.devices.taxonomy import DeviceInstance
from postwriter.graphs.metrics import DeviceMetrics
from postwriter.types import DeviceType


@dataclass
class OveruseAlert:
    """A detected overuse issue."""

    device_type: str
    severity: float  # 0-1, higher = worse
    reason: str
    evidence: dict[str, Any]


@dataclass
class UnderuseOpportunity:
    """A suggested device that might be appropriate but isn't used."""

    device_type: str
    reason: str
    appropriateness: float  # 0-1


def detect_overuse(
    metrics: DeviceMetrics,
    recurrence_caps: dict[str, int] | None = None,
) -> list[OveruseAlert]:
    """Detect device overuse from metrics.

    A device is overused if any of:
    - High local density in a short window
    - Repeated same-function same-device
    - Exceeds recurrence caps
    - High burstiness (clumped rather than distributed)
    """
    alerts: list[OveruseAlert] = []
    caps = recurrence_caps or {}

    for dtype, count in metrics.type_counts.items():
        # Check recurrence caps
        if dtype in caps and count > caps[dtype]:
            alerts.append(OveruseAlert(
                device_type=dtype,
                severity=min(1.0, (count - caps[dtype]) / max(1, caps[dtype])),
                reason=f"Exceeds recurrence cap: {count} > {caps[dtype]}",
                evidence={"count": count, "cap": caps[dtype]},
            ))

        # Check burstiness
        bust = metrics.burstiness.get(dtype, 0.0)
        if bust > 0.7 and count >= 3:
            alerts.append(OveruseAlert(
                device_type=dtype,
                severity=bust * 0.8,
                reason=f"High burstiness ({bust:.2f}): devices are clumped rather than distributed",
                evidence={"burstiness": bust, "count": count},
            ))

    # Check overall local density
    if metrics.max_local_density > 15:  # More than 15 devices per 1000 words locally
        alerts.append(OveruseAlert(
            device_type="overall",
            severity=min(1.0, metrics.max_local_density / 25),
            reason=f"High local device density: {metrics.max_local_density:.1f}/1000 words",
            evidence={"max_local_density": metrics.max_local_density},
        ))

    # Same-function same-device repetition
    if metrics.same_function_same_device > 2:
        alerts.append(OveruseAlert(
            device_type="same_function_repeat",
            severity=min(1.0, metrics.same_function_same_device / 5),
            reason=f"Same device used for same function {metrics.same_function_same_device} times",
            evidence={"count": metrics.same_function_same_device},
        ))

    # Imagery monoculture
    if metrics.imagery_concentration > 0.5 and metrics.total_instances > 5:
        alerts.append(OveruseAlert(
            device_type="imagery_monoculture",
            severity=metrics.imagery_concentration,
            reason=f"Imagery domain concentration: {metrics.imagery_concentration:.2f} (too homogeneous)",
            evidence={"concentration": metrics.imagery_concentration},
        ))

    return alerts


def suggest_underuse(
    scene_purpose: str,
    scene_conflict: str,
    current_devices: set[str],
) -> list[UnderuseOpportunity]:
    """Suggest devices that might be appropriate for a scene but aren't used.

    Conservative: only suggests when there's a clear functional match.
    """
    suggestions: list[UnderuseOpportunity] = []
    purpose_lower = scene_purpose.lower()
    conflict_lower = scene_conflict.lower()

    # Concealment/deception scenes
    if any(w in purpose_lower + conflict_lower for w in ["conceal", "hide", "secret", "deception", "lie"]):
        if "subtext_exchange" not in current_devices:
            suggestions.append(UnderuseOpportunity(
                device_type="subtext_exchange",
                reason="Concealment scene may benefit from subtext exchange",
                appropriateness=0.7,
            ))
        if "evasive_reply" not in current_devices:
            suggestions.append(UnderuseOpportunity(
                device_type="evasive_reply",
                reason="Deception scene may benefit from evasive replies",
                appropriateness=0.6,
            ))

    # Tension/confrontation scenes
    if any(w in purpose_lower + conflict_lower for w in ["confront", "tension", "argument", "clash"]):
        if "silence_beat" not in current_devices:
            suggestions.append(UnderuseOpportunity(
                device_type="silence_beat",
                reason="Confrontation may benefit from silence beats for emphasis",
                appropriateness=0.6,
            ))

    # Revelation/discovery scenes
    if any(w in purpose_lower for w in ["reveal", "discover", "realize", "understand"]):
        if "loaded_object_reference" not in current_devices:
            suggestions.append(UnderuseOpportunity(
                device_type="loaded_object_reference",
                reason="Revelation scene may benefit from loaded object references",
                appropriateness=0.5,
            ))

    return suggestions
