"""Scans a context/ directory for markdown and image files that inform the writing task.

Users can optionally add YAML frontmatter to classify files:

    ---
    type: sample_writing
    ---
    Content here...

Supported types: sample_writing, plot, guidelines, characters, world, style, reference.
If no frontmatter, the system infers purpose from filename and content.
"""

from __future__ import annotations

import enum
import hashlib
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Frontmatter regex: matches --- ... --- at the start of a file
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Image extensions we support (will be passed to vision-capable model calls)
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

# Markdown extensions
MARKDOWN_EXTENSIONS = {".md", ".markdown", ".txt"}

# Filename patterns for type inference
_FILENAME_PATTERNS: list[tuple[re.Pattern[str], "ContextType"]] = []


class ContextType(str, enum.Enum):
    SAMPLE_WRITING = "sample_writing"
    PLOT = "plot"
    GUIDELINES = "guidelines"
    CHARACTERS = "characters"
    WORLD = "world"
    STYLE = "style"
    REFERENCE = "reference"
    IMAGE = "image"
    UNKNOWN = "unknown"


# Build filename inference patterns
_INFERENCE_MAP: dict[str, ContextType] = {
    "sample": ContextType.SAMPLE_WRITING,
    "writing": ContextType.SAMPLE_WRITING,
    "excerpt": ContextType.SAMPLE_WRITING,
    "draft": ContextType.SAMPLE_WRITING,
    "plot": ContextType.PLOT,
    "outline": ContextType.PLOT,
    "synopsis": ContextType.PLOT,
    "story": ContextType.PLOT,
    "guideline": ContextType.GUIDELINES,
    "rule": ContextType.GUIDELINES,
    "instruction": ContextType.GUIDELINES,
    "character": ContextType.CHARACTERS,
    "cast": ContextType.CHARACTERS,
    "protagonist": ContextType.CHARACTERS,
    "antagonist": ContextType.CHARACTERS,
    "world": ContextType.WORLD,
    "setting": ContextType.WORLD,
    "lore": ContextType.WORLD,
    "map": ContextType.WORLD,
    "geography": ContextType.WORLD,
    "style": ContextType.STYLE,
    "voice": ContextType.STYLE,
    "tone": ContextType.STYLE,
    "reference": ContextType.REFERENCE,
    "research": ContextType.REFERENCE,
    "notes": ContextType.REFERENCE,
}


@dataclass
class ContextFile:
    """A single loaded context file."""

    path: Path
    context_type: ContextType
    content: str  # Text content for markdown; empty for images
    is_image: bool = False
    frontmatter: dict[str, Any] = field(default_factory=dict)
    content_hash: str = ""

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def stem(self) -> str:
        return self.path.stem


@dataclass
class ContextManifest:
    """Records which context files were active at a point in time."""

    files: list[dict[str, str]] = field(default_factory=list)

    def snapshot(self, loaded_files: list[ContextFile]) -> None:
        self.files = [
            {
                "path": str(f.path),
                "type": f.context_type.value,
                "hash": f.content_hash,
            }
            for f in loaded_files
        ]

    def to_dict(self) -> list[dict[str, str]]:
        return self.files


class ContextLoader:
    """Loads and manages context files from a project directory.

    Usage:
        loader = ContextLoader(project_dir / "context")
        files = loader.load()
        # Later, to detect new files:
        new_files = loader.refresh()
    """

    def __init__(self, context_dir: Path) -> None:
        self._dir = context_dir
        self._loaded: dict[Path, ContextFile] = {}
        self._manifest = ContextManifest()

    @property
    def context_dir(self) -> Path:
        return self._dir

    @property
    def files(self) -> list[ContextFile]:
        return list(self._loaded.values())

    @property
    def manifest(self) -> ContextManifest:
        return self._manifest

    def load(self) -> list[ContextFile]:
        """Scan the context directory and load all recognized files.

        Returns all loaded files. Silently returns empty list if directory
        doesn't exist.
        """
        if not self._dir.exists() or not self._dir.is_dir():
            logger.debug("No context directory at %s", self._dir)
            return []

        loaded: list[ContextFile] = []
        for path in sorted(self._dir.iterdir()):
            if path.is_file() and not path.name.startswith("."):
                cf = self._load_file(path)
                if cf:
                    self._loaded[path] = cf
                    loaded.append(cf)

        self._manifest.snapshot(loaded)
        if loaded:
            logger.info(
                "Loaded %d context file(s) from %s", len(loaded), self._dir
            )
        return loaded

    def refresh(self) -> list[ContextFile]:
        """Re-scan and return only new or changed files since last load."""
        if not self._dir.exists() or not self._dir.is_dir():
            return []

        new_or_changed: list[ContextFile] = []
        current_paths: set[Path] = set()

        for path in sorted(self._dir.iterdir()):
            if path.is_file() and not path.name.startswith("."):
                current_paths.add(path)
                cf = self._load_file(path)
                if cf is None:
                    continue

                existing = self._loaded.get(path)
                if existing is None or existing.content_hash != cf.content_hash:
                    self._loaded[path] = cf
                    new_or_changed.append(cf)

        # Remove files that were deleted
        for removed in set(self._loaded.keys()) - current_paths:
            del self._loaded[removed]

        self._manifest.snapshot(list(self._loaded.values()))
        return new_or_changed

    def get_by_type(self, context_type: ContextType) -> list[ContextFile]:
        """Return all loaded files of a given type."""
        return [f for f in self._loaded.values() if f.context_type == context_type]

    def get_text_content(self, context_type: ContextType | None = None) -> str:
        """Get concatenated text content, optionally filtered by type."""
        files = self.get_by_type(context_type) if context_type else self.files
        parts = []
        for f in files:
            if not f.is_image and f.content:
                parts.append(f"## {f.name} ({f.context_type.value})\n\n{f.content}")
        return "\n\n---\n\n".join(parts)

    def get_images(self) -> list[ContextFile]:
        """Return all loaded image files."""
        return [f for f in self._loaded.values() if f.is_image]

    def summary(self) -> str:
        """Human-readable summary of loaded context files."""
        if not self._loaded:
            return "No context files found."

        by_type: dict[ContextType, list[str]] = {}
        for f in self._loaded.values():
            by_type.setdefault(f.context_type, []).append(f.name)

        parts = [f"Found {len(self._loaded)} context file(s):"]
        for ct, names in sorted(by_type.items(), key=lambda x: x[0].value):
            label = ct.value.replace("_", " ")
            parts.append(f"  {label}: {', '.join(names)}")
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _load_file(self, path: Path) -> ContextFile | None:
        suffix = path.suffix.lower()

        if suffix in IMAGE_EXTENSIONS:
            content_hash = self._hash_file(path)
            return ContextFile(
                path=path,
                context_type=ContextType.IMAGE,
                content="",
                is_image=True,
                content_hash=content_hash,
            )

        if suffix in MARKDOWN_EXTENSIONS:
            try:
                raw = path.read_text(encoding="utf-8")
            except Exception as e:
                logger.warning("Failed to read %s: %s", path, e)
                return None

            content_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]
            frontmatter, content = self._parse_frontmatter(raw)
            context_type = self._determine_type(path, frontmatter, content)

            return ContextFile(
                path=path,
                context_type=context_type,
                content=content,
                is_image=False,
                frontmatter=frontmatter,
                content_hash=content_hash,
            )

        # Skip unrecognized file types
        return None

    @staticmethod
    def _parse_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
        """Extract YAML frontmatter and body content."""
        match = _FRONTMATTER_RE.match(raw)
        if not match:
            return {}, raw

        fm_text = match.group(1)
        content = raw[match.end():]

        # Simple key: value parsing (avoid requiring PyYAML dependency)
        frontmatter: dict[str, Any] = {}
        for line in fm_text.strip().split("\n"):
            line = line.strip()
            if ":" in line:
                key, _, value = line.partition(":")
                frontmatter[key.strip()] = value.strip()

        return frontmatter, content

    @staticmethod
    def _determine_type(
        path: Path, frontmatter: dict[str, Any], content: str
    ) -> ContextType:
        """Determine the context type from frontmatter or filename inference."""
        # Check frontmatter first
        fm_type = frontmatter.get("type", "").lower().strip()
        if fm_type:
            try:
                return ContextType(fm_type)
            except ValueError:
                pass

        # Infer from filename
        stem_lower = path.stem.lower().replace("-", " ").replace("_", " ")
        for keyword, ct in _INFERENCE_MAP.items():
            if keyword in stem_lower:
                return ct

        return ContextType.UNKNOWN

    @staticmethod
    def _hash_file(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
