"""Export manuscript as markdown."""

from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from postwriter.canon.store import CanonStore
from postwriter.models.core import SceneDraft


async def export_markdown(
    session: AsyncSession,
    manuscript_id: uuid.UUID,
    output_path: Path | None = None,
) -> str:
    """Export the full manuscript as markdown.

    Returns the markdown string and optionally writes to a file.
    """
    store = CanonStore(session)
    manuscript = await store.get_manuscript(manuscript_id)
    if not manuscript:
        return ""

    parts: list[str] = []
    parts.append(f"# {manuscript.title}\n")

    chapters = await store.get_all_chapters(manuscript_id)
    total_words = 0

    for chapter in chapters:
        # Chapter heading
        title = chapter.title or f"Chapter {chapter.ordinal}"
        parts.append(f"\n## {title}\n")

        scenes = await store.get_scenes(chapter.id)
        for scene in scenes:
            if scene.accepted_draft_id:
                draft = await session.get(SceneDraft, scene.accepted_draft_id)
                if draft and draft.prose:
                    parts.append(draft.prose)
                    parts.append("")  # Blank line between scenes
                    total_words += draft.word_count

    # Add word count at the end
    parts.append(f"\n---\n*{total_words:,} words*\n")

    text = "\n".join(parts)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")

    return text
