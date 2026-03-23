"""Device ecology audit: manuscript-level device distribution analysis."""

from __future__ import annotations

from collections import Counter
from typing import Any

from postwriter.devices.taxonomy import DeviceInstance
from postwriter.revision.base import RevisionProposal


class DeviceEcologyAudit:
    """Audits device ecology across the full manuscript."""

    name = "device_ecology"

    async def audit(self, manuscript_data: dict[str, Any]) -> list[RevisionProposal]:
        proposals: list[RevisionProposal] = []
        chapters = manuscript_data.get("chapter_devices", {})

        if not chapters:
            return proposals

        # Collect all instances across manuscript
        all_instances: list[DeviceInstance] = []
        chapter_type_counts: list[Counter[str]] = []

        for ch_id, ch_data in chapters.items():
            instances = ch_data.get("instances", [])
            all_instances.extend(instances)
            type_count: Counter[str] = Counter()
            for inst in instances:
                dtype = inst.device_type.value if isinstance(inst, DeviceInstance) else inst.get("device_type", "")
                type_count[dtype] += 1
            chapter_type_counts.append(type_count)

        if not all_instances:
            return proposals

        # Check for narrator tics: same device appearing in most chapters
        total_chapters = len(chapters)
        overall_counts: Counter[str] = Counter()
        chapter_presence: Counter[str] = Counter()

        for tc in chapter_type_counts:
            for dtype in tc:
                overall_counts[dtype] += tc[dtype]
                chapter_presence[dtype] += 1

        for dtype, presence in chapter_presence.items():
            if presence / total_chapters > 0.8 and overall_counts[dtype] > total_chapters * 2:
                proposals.append(RevisionProposal(
                    audit_name=self.name,
                    severity=0.5,
                    description=(
                        f"Narrator tic: '{dtype}' appears in {presence}/{total_chapters} chapters "
                        f"({overall_counts[dtype]} total occurrences)"
                    ),
                    proposed_action=(
                        f"Vary the use of '{dtype}' — it's becoming a crutch. "
                        "Consider substituting with different devices that serve the same function."
                    ),
                    evidence={"device": dtype, "count": overall_counts[dtype], "chapters": presence},
                ))

        # Check for chapter-opening/closing repetition
        opening_devices: Counter[str] = Counter()
        closing_devices: Counter[str] = Counter()

        for ch_data in chapters.values():
            instances = ch_data.get("instances", [])
            if not instances:
                continue
            # Devices in first 500 chars
            for inst in instances:
                pos = inst.span_start if isinstance(inst, DeviceInstance) else inst.get("span_start", 0)
                dtype = inst.device_type.value if isinstance(inst, DeviceInstance) else inst.get("device_type", "")
                if pos < 500:
                    opening_devices[dtype] += 1
                if pos > ch_data.get("word_count", 5000) * 5 - 500:  # Approximate end
                    closing_devices[dtype] += 1

        for dtype, count in opening_devices.items():
            if count > total_chapters * 0.6:
                proposals.append(RevisionProposal(
                    audit_name=self.name,
                    severity=0.4,
                    description=f"Repetitive chapter openings: '{dtype}' used in {count} chapter openings",
                    proposed_action="Vary chapter opening strategies to prevent pattern fatigue.",
                    evidence={"device": dtype, "opening_count": count},
                ))

        return proposals
