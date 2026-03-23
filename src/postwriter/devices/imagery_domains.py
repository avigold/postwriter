"""Imagery domain classification for figurative language."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

from postwriter.devices.taxonomy import DeviceInstance
from postwriter.types import DeviceType

# Common imagery domain keywords
DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "water": ["water", "ocean", "sea", "river", "wave", "tide", "flood", "drown", "current", "shore", "rain", "storm", "pool", "stream", "lake", "deep", "surface", "flow"],
    "fire": ["fire", "flame", "burn", "ash", "ember", "smoke", "blaze", "heat", "scorch", "ignite", "spark", "smolder", "char"],
    "light": ["light", "shadow", "dark", "bright", "glow", "shine", "dim", "illuminate", "gleam", "flicker", "luminous", "radiant", "pale"],
    "architecture": ["wall", "door", "window", "room", "house", "foundation", "ceiling", "floor", "corridor", "threshold", "frame", "structure", "bridge", "tower"],
    "body": ["blood", "bone", "skin", "heart", "hand", "eye", "breath", "muscle", "nerve", "vein", "stomach", "spine", "throat", "face"],
    "nature": ["tree", "root", "branch", "leaf", "seed", "flower", "soil", "stone", "mountain", "wind", "sky", "earth", "forest", "garden"],
    "animal": ["wolf", "bird", "snake", "fish", "dog", "cat", "hawk", "prey", "hunt", "nest", "wing", "claw", "flock", "herd"],
    "machine": ["engine", "gear", "wheel", "wire", "circuit", "mechanism", "system", "machine", "device", "lever", "valve", "motor"],
    "cloth": ["thread", "fabric", "weave", "stitch", "tear", "unravel", "knit", "pattern", "cloth", "silk", "wool", "seam"],
    "glass": ["glass", "mirror", "reflection", "transparent", "shatter", "crystal", "lens", "prism", "fragile", "crack"],
    "weather": ["storm", "cloud", "fog", "mist", "frost", "ice", "snow", "thunder", "lightning", "wind", "chill", "heat"],
    "music": ["rhythm", "melody", "chord", "harmony", "discord", "note", "tune", "beat", "silence", "echo", "resonance"],
    "war": ["battle", "weapon", "armor", "siege", "retreat", "advance", "wound", "defend", "attack", "surrender", "truce"],
    "journey": ["path", "road", "journey", "destination", "crossroads", "map", "compass", "wander", "lost", "direction", "horizon"],
}


@dataclass
class ImageryProfile:
    """Summary of imagery domain usage."""

    domain_counts: dict[str, int] = field(default_factory=dict)
    total_figurative: int = 0
    dominant_domain: str | None = None
    domain_diversity: float = 0.0  # 0 = monoculture, 1 = evenly distributed

    def concentration_index(self) -> float:
        """Herfindahl-Hirschman-style concentration. 1 = all one domain, 0 = evenly spread."""
        if not self.domain_counts or self.total_figurative == 0:
            return 0.0
        shares = [c / self.total_figurative for c in self.domain_counts.values()]
        return sum(s * s for s in shares)


class ImageryDomainClassifier:
    """Classifies figurative device instances into imagery source domains."""

    def classify_instance(self, instance: DeviceInstance) -> str | None:
        """Determine the imagery domain of a single device instance."""
        # If already classified by model detector
        if instance.imagery_domain:
            return self._normalize_domain(instance.imagery_domain)

        # Only classify figurative devices
        if instance.device_type not in (
            DeviceType.METAPHOR, DeviceType.SIMILE, DeviceType.PERSONIFICATION,
            DeviceType.METONYMY, DeviceType.SYNECDOCHE,
        ):
            return None

        return self._infer_domain(instance.text)

    def classify_all(self, instances: list[DeviceInstance]) -> list[DeviceInstance]:
        """Classify and annotate all instances with imagery domains."""
        for inst in instances:
            domain = self.classify_instance(inst)
            if domain:
                inst.imagery_domain = domain
        return instances

    def profile(self, instances: list[DeviceInstance]) -> ImageryProfile:
        """Build an imagery profile from a set of device instances."""
        figurative = [
            i for i in instances
            if i.device_type in (
                DeviceType.METAPHOR, DeviceType.SIMILE, DeviceType.PERSONIFICATION,
                DeviceType.METONYMY, DeviceType.SYNECDOCHE, DeviceType.HYPERBOLE,
            )
        ]

        domain_counts: Counter[str] = Counter()
        for inst in figurative:
            domain = inst.imagery_domain or self._infer_domain(inst.text)
            if domain:
                domain_counts[domain] += 1

        total = len(figurative)
        profile = ImageryProfile(
            domain_counts=dict(domain_counts),
            total_figurative=total,
        )

        if domain_counts:
            profile.dominant_domain = domain_counts.most_common(1)[0][0]
            n_domains = len(domain_counts)
            profile.domain_diversity = (
                1.0 - profile.concentration_index() if n_domains > 1 else 0.0
            )

        return profile

    @staticmethod
    def _infer_domain(text: str) -> str | None:
        """Infer imagery domain from text keywords."""
        text_lower = text.lower()
        scores: dict[str, int] = {}
        for domain, keywords in DOMAIN_KEYWORDS.items():
            count = sum(1 for kw in keywords if re.search(rf"\b{kw}\b", text_lower))
            if count > 0:
                scores[domain] = count

        if scores:
            return max(scores, key=scores.get)  # type: ignore[arg-type]
        return None

    @staticmethod
    def _normalize_domain(domain: str) -> str:
        """Normalize domain name to a canonical form."""
        domain = domain.lower().strip()
        # Map common variants
        variants: dict[str, str] = {
            "aquatic": "water", "marine": "water", "ocean": "water",
            "flame": "fire", "combustion": "fire",
            "darkness": "light", "brightness": "light",
            "building": "architecture", "structural": "architecture",
            "corporeal": "body", "physical": "body",
            "botanical": "nature", "organic": "nature",
            "mechanical": "machine", "industrial": "machine",
            "textile": "cloth",
            "meteorological": "weather", "atmospheric": "weather",
            "martial": "war", "military": "war",
            "travel": "journey", "navigation": "journey",
        }
        return variants.get(domain, domain)
