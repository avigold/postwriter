"""Temporal device graph: tracks device frequency over scenes and chapters."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

from postwriter.devices.taxonomy import DeviceInstance
from postwriter.types import DeviceType


@dataclass
class SceneDeviceData:
    """Device data for a single scene."""

    scene_id: str
    chapter_id: str
    scene_ordinal: int
    chapter_ordinal: int
    word_count: int = 0
    instances: list[DeviceInstance] = field(default_factory=list)

    @property
    def device_counts(self) -> Counter[DeviceType]:
        return Counter(i.device_type for i in self.instances)

    @property
    def density_per_1000(self) -> float:
        if self.word_count == 0:
            return 0.0
        return len(self.instances) / self.word_count * 1000


class TemporalGraph:
    """Tracks device usage over the manuscript timeline (scene by scene).

    Not a graph database — just an ordered collection with temporal analytics.
    """

    def __init__(self) -> None:
        self._scenes: list[SceneDeviceData] = []
        self._by_chapter: dict[str, list[SceneDeviceData]] = defaultdict(list)

    def add_scene(self, data: SceneDeviceData) -> None:
        self._scenes.append(data)
        self._by_chapter[data.chapter_id].append(data)

    @property
    def scene_count(self) -> int:
        return len(self._scenes)

    def device_frequency_over_time(self, device_type: DeviceType) -> list[tuple[int, int]]:
        """Return (scene_ordinal, count) pairs for a specific device type."""
        return [
            (s.scene_ordinal, s.device_counts.get(device_type, 0))
            for s in self._scenes
        ]

    def density_over_time(self) -> list[tuple[int, float]]:
        """Return (scene_ordinal, density_per_1000) for overall device density."""
        return [(s.scene_ordinal, s.density_per_1000) for s in self._scenes]

    def rolling_window_density(
        self, device_type: DeviceType, window_size: int = 5
    ) -> list[tuple[int, float]]:
        """Compute rolling average density for a device type."""
        counts = [s.device_counts.get(device_type, 0) for s in self._scenes]
        words = [s.word_count for s in self._scenes]

        results = []
        for i in range(len(counts)):
            start = max(0, i - window_size + 1)
            window_counts = sum(counts[start:i + 1])
            window_words = sum(words[start:i + 1])
            density = (window_counts / window_words * 1000) if window_words > 0 else 0.0
            results.append((self._scenes[i].scene_ordinal, density))
        return results

    def chapter_summary(self) -> list[dict[str, Any]]:
        """Summary per chapter: total devices, density, top device types."""
        summaries = []
        for ch_id, scenes in self._by_chapter.items():
            total_instances = sum(len(s.instances) for s in scenes)
            total_words = sum(s.word_count for s in scenes)
            all_types: Counter[DeviceType] = Counter()
            for s in scenes:
                all_types.update(s.device_counts)

            summaries.append({
                "chapter_id": ch_id,
                "chapter_ordinal": scenes[0].chapter_ordinal if scenes else 0,
                "total_devices": total_instances,
                "total_words": total_words,
                "density_per_1000": (total_instances / total_words * 1000) if total_words > 0 else 0,
                "top_devices": all_types.most_common(5),
            })
        summaries.sort(key=lambda x: x["chapter_ordinal"])
        return summaries
