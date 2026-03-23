"""Export manuscript as EPUB."""

from __future__ import annotations

import uuid
from pathlib import Path

from ebooklib import epub
from sqlalchemy.ext.asyncio import AsyncSession

from postwriter.canon.store import CanonStore
from postwriter.models.core import SceneDraft

# Basic CSS for readable typography
BOOK_CSS = """
body {
    font-family: Georgia, "Times New Roman", serif;
    line-height: 1.6;
    margin: 2em;
    color: #1a1a1a;
}
h1 {
    font-size: 1.8em;
    margin-top: 2em;
    margin-bottom: 0.5em;
    font-weight: normal;
}
h2 {
    font-size: 1.3em;
    margin-top: 2em;
    margin-bottom: 0.5em;
    font-weight: normal;
    font-style: italic;
}
p {
    margin: 0.8em 0;
    text-align: justify;
    text-indent: 1.5em;
    hyphens: auto;
    -webkit-hyphens: auto;
}
p:first-of-type {
    text-indent: 0;
}
.scene-break {
    text-align: center;
    margin: 2em 0;
    font-size: 1.2em;
    color: #666;
}
"""


async def export_epub(
    session: AsyncSession,
    manuscript_id: uuid.UUID,
    output_path: Path | None = None,
    author: str = "Postwriter",
    language: str = "en",
) -> Path | None:
    """Export the full manuscript as an EPUB file.

    Returns the path to the generated EPUB, or None if the manuscript
    doesn't exist.
    """
    store = CanonStore(session)
    manuscript = await store.get_manuscript(manuscript_id)
    if not manuscript:
        return None

    book = epub.EpubBook()

    # Metadata
    book.set_identifier(str(manuscript_id))
    book.set_title(manuscript.title or "Untitled")
    book.set_language(language)
    book.add_author(author)

    # Stylesheet
    css = epub.EpubItem(
        uid="style",
        file_name="style/default.css",
        media_type="text/css",
        content=BOOK_CSS.encode("utf-8"),
    )
    book.add_item(css)

    # Build chapters
    chapters = await store.get_all_chapters(manuscript_id)
    epub_chapters = []
    spine = ["nav"]

    for chapter in chapters:
        title = chapter.title or f"Chapter {chapter.ordinal}"
        scenes = await store.get_scenes(chapter.id)

        # Collect prose from accepted drafts
        scene_htmls = []
        for i, scene in enumerate(scenes):
            if scene.accepted_draft_id:
                draft = await session.get(SceneDraft, scene.accepted_draft_id)
                if draft and draft.prose:
                    # Convert prose to HTML paragraphs
                    paragraphs = _prose_to_html(draft.prose)
                    scene_htmls.append(paragraphs)
                    # Add scene break between scenes (except after last)
                    if i < len(scenes) - 1:
                        scene_htmls.append('<p class="scene-break">* * *</p>')

        if not scene_htmls:
            continue

        # Build chapter XHTML
        body = "\n".join(scene_htmls)
        html = f"<h1>{title}</h1>\n{body}"

        ch = epub.EpubHtml(
            title=title,
            file_name=f"chapter_{chapter.ordinal:03d}.xhtml",
            lang=language,
        )
        ch.content = html.encode("utf-8")
        ch.add_item(css)

        book.add_item(ch)
        epub_chapters.append(ch)
        spine.append(ch)

    # Table of contents
    book.toc = epub_chapters

    # Navigation
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Spine (reading order)
    book.spine = spine

    # Write
    if output_path is None:
        output_path = Path("output") / f"{_safe_filename(manuscript.title)}.epub"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(output_path), book)

    return output_path


def _prose_to_html(prose: str) -> str:
    """Convert plain prose text to HTML paragraphs."""
    import html

    lines = prose.strip().split("\n")
    paragraphs = []
    current = []

    for line in lines:
        line = line.strip()
        if not line:
            if current:
                text = " ".join(current)
                paragraphs.append(f"<p>{html.escape(text)}</p>")
                current = []
        else:
            current.append(line)

    if current:
        text = " ".join(current)
        paragraphs.append(f"<p>{html.escape(text)}</p>")

    return "\n".join(paragraphs)


def _safe_filename(title: str | None) -> str:
    """Convert a title to a safe filename."""
    if not title:
        return "manuscript"
    import re
    safe = re.sub(r"[^\w\s-]", "", title.lower())
    return re.sub(r"[\s]+", "-", safe).strip("-")[:50]
