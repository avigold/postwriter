"""Export full canonical state as JSON."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from postwriter.canon.store import CanonStore


async def export_json(
    session: AsyncSession,
    manuscript_id: uuid.UUID,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Export full canonical state as a JSON-serializable dict."""
    store = CanonStore(session)
    manuscript = await store.get_manuscript(manuscript_id)
    if not manuscript:
        return {}

    characters = await store.get_characters(manuscript_id)
    chapters = await store.get_all_chapters(manuscript_id)
    promises = await store.get_promises(manuscript_id)
    themes = await store.get_themes(manuscript_id)
    style = await store.get_default_style_profile(manuscript_id)

    # Build chapter/scene tree
    chapter_data = []
    for ch in chapters:
        scenes = await store.get_scenes(ch.id)
        scene_data = []
        for s in scenes:
            drafts = await store.get_drafts(s.id)
            scene_data.append({
                "id": str(s.id),
                "ordinal": s.ordinal,
                "location": s.location,
                "purpose": s.purpose,
                "conflict": s.conflict,
                "status": s.status.value,
                "is_pivotal": s.is_pivotal,
                "state_mutations": s.state_mutations,
                "drafts": [
                    {
                        "id": str(d.id),
                        "branch_label": d.branch_label,
                        "branch_status": d.branch_status.value,
                        "word_count": d.word_count,
                        "prose": d.prose,
                    }
                    for d in drafts
                ],
            })
        chapter_data.append({
            "id": str(ch.id),
            "ordinal": ch.ordinal,
            "title": ch.title,
            "function": ch.function,
            "scenes": scene_data,
        })

    data = {
        "manuscript": {
            "id": str(manuscript.id),
            "title": manuscript.title,
            "premise": manuscript.premise,
            "controlling_design": manuscript.controlling_design,
            "status": manuscript.status.value,
        },
        "characters": [
            {
                "id": str(c.id),
                "name": c.name,
                "aliases": c.aliases,
                "biography": c.biography,
                "motives": c.motives,
                "fears": c.fears,
                "desires": c.desires,
                "secrets": c.secrets,
                "speaking_traits": c.speaking_traits,
                "arc_hypotheses": c.arc_hypotheses,
                "is_pov": c.is_pov_character,
            }
            for c in characters
        ],
        "chapters": chapter_data,
        "promises": [
            {
                "id": str(p.id),
                "type": p.type.value,
                "description": p.description,
                "salience": p.salience,
                "status": p.status.value,
                "payoff_strength": p.payoff_strength,
            }
            for p in promises
        ],
        "themes": [
            {
                "id": str(t.id),
                "name": t.name,
                "description": t.description,
                "overstatement_risk": t.overstatement_risk,
            }
            for t in themes
        ],
        "style_profile": {
            "voice_description": style.voice_description if style else "",
            "banned_phrases": style.banned_phrases if style else [],
        },
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(data, indent=2, default=str),
            encoding="utf-8",
        )

    return data
