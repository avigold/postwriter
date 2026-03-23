"""Rhythm audit: detects sentence/paragraph/dialogue monotony across chapters."""

from __future__ import annotations

import statistics
from typing import Any

from postwriter.devices.detectors.rhythm import RhythmProfile
from postwriter.revision.base import RevisionProposal


class RhythmAudit:
    """Audits prose rhythm across the manuscript for monotony."""

    name = "rhythm_audit"

    async def audit(self, manuscript_data: dict[str, Any]) -> list[RevisionProposal]:
        proposals: list[RevisionProposal] = []
        chapter_rhythms: list[dict[str, Any]] = manuscript_data.get("chapter_rhythms", [])

        if len(chapter_rhythms) < 3:
            return proposals

        # Check sentence length monotony across chapters
        avg_lengths = [r.get("avg_sentence_length", 0) for r in chapter_rhythms if r.get("avg_sentence_length")]
        if len(avg_lengths) >= 3:
            std = statistics.stdev(avg_lengths)
            if std < 2.0:  # Very similar sentence lengths across chapters
                proposals.append(RevisionProposal(
                    audit_name=self.name,
                    severity=0.5,
                    description=(
                        f"Sentence length monotony: average sentence length varies by only "
                        f"{std:.1f} words across chapters (range: {min(avg_lengths):.0f}-{max(avg_lengths):.0f})"
                    ),
                    proposed_action=(
                        "Vary prose rhythm between chapters. Some chapters should use shorter, "
                        "more clipped sentences; others should allow longer, more complex constructions."
                    ),
                    evidence={"std": std, "avg_lengths": avg_lengths},
                ))

        # Check dialogue ratio stagnation
        dialogue_pcts = [r.get("dialogue_pct", 0) for r in chapter_rhythms]
        if len(dialogue_pcts) >= 3:
            dial_std = statistics.stdev(dialogue_pcts)
            if dial_std < 0.05:  # Very similar dialogue ratios
                proposals.append(RevisionProposal(
                    audit_name=self.name,
                    severity=0.4,
                    description=(
                        f"Dialogue ratio stagnation: dialogue percentage varies by only "
                        f"{dial_std:.1%} across chapters"
                    ),
                    proposed_action=(
                        "Vary the dialogue/narration balance. Some chapters should be "
                        "dialogue-heavy; others should be predominantly narrated."
                    ),
                    evidence={"std": dial_std, "dialogue_pcts": dialogue_pcts},
                ))

        # Check rhythm variation scores
        variation_scores = [r.get("rhythm_variation", 0.5) for r in chapter_rhythms]
        low_variation = [
            (i, v) for i, v in enumerate(variation_scores) if v < 0.3
        ]
        if len(low_variation) > len(chapter_rhythms) * 0.3:
            proposals.append(RevisionProposal(
                audit_name=self.name,
                severity=0.5,
                description=(
                    f"{len(low_variation)} chapters have low rhythm variation "
                    f"(< 0.3 score), suggesting monotonous prose movement"
                ),
                proposed_action=(
                    "Introduce more sentence length variation in flagged chapters. "
                    "Mix short punchy sentences with longer periodic constructions."
                ),
                target_chapter_ids=[
                    chapter_rhythms[i].get("chapter_id", "") for i, _ in low_variation
                ],
                evidence={"low_variation_chapters": low_variation},
            ))

        return proposals
