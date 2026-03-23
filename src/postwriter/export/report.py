"""Generation report: token usage, timing, decisions, scores."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from postwriter.canon.store import CanonStore
from postwriter.llm.budget import TokenBudget
from postwriter.models.core import Scene, SceneDraft
from postwriter.models.events import Event
from postwriter.types import BranchStatus, SceneStatus


async def export_report(
    session: AsyncSession,
    manuscript_id: uuid.UUID,
    budget: TokenBudget | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Generate a report on the manuscript generation process."""
    store = CanonStore(session)
    manuscript = await store.get_manuscript(manuscript_id)
    if not manuscript:
        return {}

    chapters = await store.get_all_chapters(manuscript_id)

    # Count scenes and words
    total_scenes = 0
    accepted_scenes = 0
    total_words = 0
    total_drafts = 0
    pivotal_scenes = 0

    for ch in chapters:
        scenes = await store.get_scenes(ch.id)
        for s in scenes:
            total_scenes += 1
            if s.status == SceneStatus.ACCEPTED:
                accepted_scenes += 1
            if s.is_pivotal:
                pivotal_scenes += 1
            drafts = await store.get_drafts(s.id)
            total_drafts += len(drafts)
            for d in drafts:
                if d.branch_status == BranchStatus.SELECTED:
                    total_words += d.word_count

    # Count events
    event_count_result = await session.execute(
        select(func.count(Event.id)).where(Event.manuscript_id == manuscript_id)
    )
    event_count = event_count_result.scalar_one()

    # Branch statistics
    selected_drafts = await session.execute(
        select(SceneDraft.branch_label, func.count(SceneDraft.id))
        .join(Scene, Scene.id == SceneDraft.scene_id)
        .join(
            __import__("postwriter.models.core", fromlist=["Chapter"]).Chapter,
            Scene.chapter_id == __import__("postwriter.models.core", fromlist=["Chapter"]).Chapter.id,
        )
        .where(SceneDraft.branch_status == BranchStatus.SELECTED)
        .group_by(SceneDraft.branch_label)
    )
    branch_selections: dict[str, int] = {}
    try:
        for row in selected_drafts:
            branch_selections[row[0]] = row[1]
    except Exception:
        pass  # Complex query may fail, not critical

    report: dict[str, Any] = {
        "manuscript": {
            "id": str(manuscript_id),
            "title": manuscript.title,
            "status": manuscript.status.value,
        },
        "statistics": {
            "total_chapters": len(chapters),
            "total_scenes": total_scenes,
            "accepted_scenes": accepted_scenes,
            "pivotal_scenes": pivotal_scenes,
            "total_drafts_generated": total_drafts,
            "total_words": total_words,
            "drafts_per_scene": round(total_drafts / max(1, total_scenes), 1),
            "avg_words_per_scene": round(total_words / max(1, accepted_scenes)),
            "total_events": event_count,
        },
        "branch_selections": branch_selections,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    if budget:
        report["token_usage"] = budget.summary()

    report_text = _format_report(report)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_text, encoding="utf-8")

    return report


def _format_report(report: dict[str, Any]) -> str:
    """Format report as readable text."""
    lines = [
        f"# Generation Report: {report['manuscript']['title']}",
        f"Generated: {report['generated_at']}",
        f"Status: {report['manuscript']['status']}",
        "",
        "## Statistics",
    ]

    stats = report["statistics"]
    lines.extend([
        f"- Chapters: {stats['total_chapters']}",
        f"- Scenes: {stats['total_scenes']} ({stats['accepted_scenes']} accepted, {stats['pivotal_scenes']} pivotal)",
        f"- Total drafts generated: {stats['total_drafts_generated']}",
        f"- Drafts per scene: {stats['drafts_per_scene']}",
        f"- Total words: {stats['total_words']:,}",
        f"- Avg words per scene: {stats['avg_words_per_scene']:,}",
        f"- Total events logged: {stats['total_events']}",
    ])

    if report.get("branch_selections"):
        lines.extend(["", "## Branch Selection Distribution"])
        for label, count in sorted(report["branch_selections"].items(), key=lambda x: -x[1]):
            lines.append(f"- {label}: {count}")

    if report.get("token_usage"):
        lines.extend(["", "## Token Usage"])
        for tier, usage in report["token_usage"].items():
            lines.append(
                f"- {tier}: {usage['total_tokens']:,} tokens "
                f"({usage['calls']} calls, "
                f"remaining: {usage['remaining'] if usage['remaining'] is not None else 'unlimited'})"
            )

    return "\n".join(lines)
