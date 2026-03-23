"""Rhythm analyzer: computes prose rhythm metrics (no LLM needed)."""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass, field


@dataclass
class RhythmProfile:
    """Rhythm analysis of a prose passage."""

    sentence_count: int = 0
    word_count: int = 0
    paragraph_count: int = 0

    # Sentence length stats
    sentence_lengths: list[int] = field(default_factory=list)
    avg_sentence_length: float = 0.0
    sentence_length_std: float = 0.0
    min_sentence_length: int = 0
    max_sentence_length: int = 0
    short_sentence_pct: float = 0.0  # <= 8 words
    medium_sentence_pct: float = 0.0  # 9-20 words
    long_sentence_pct: float = 0.0  # > 20 words

    # Paragraph stats
    paragraph_lengths: list[int] = field(default_factory=list)
    avg_paragraph_length: float = 0.0

    # Dialogue
    dialogue_word_count: int = 0
    dialogue_pct: float = 0.0

    # Punctuation density
    comma_density: float = 0.0  # per 100 words
    semicolon_density: float = 0.0
    dash_density: float = 0.0
    question_density: float = 0.0
    exclamation_density: float = 0.0

    # Variation score (0-1, higher = more varied)
    rhythm_variation: float = 0.0


class RhythmAnalyzer:
    """Analyzes prose rhythm without LLM calls."""

    def analyze(self, prose: str) -> RhythmProfile:
        profile = RhythmProfile()

        if not prose.strip():
            return profile

        # Word and sentence counts
        words = prose.split()
        profile.word_count = len(words)
        sentences = self._split_sentences(prose)
        profile.sentence_count = len(sentences)

        # Sentence lengths
        profile.sentence_lengths = [len(s.split()) for s in sentences]
        if profile.sentence_lengths:
            profile.avg_sentence_length = statistics.mean(profile.sentence_lengths)
            profile.sentence_length_std = (
                statistics.stdev(profile.sentence_lengths)
                if len(profile.sentence_lengths) > 1
                else 0.0
            )
            profile.min_sentence_length = min(profile.sentence_lengths)
            profile.max_sentence_length = max(profile.sentence_lengths)

            short = sum(1 for l in profile.sentence_lengths if l <= 8)
            medium = sum(1 for l in profile.sentence_lengths if 9 <= l <= 20)
            long = sum(1 for l in profile.sentence_lengths if l > 20)
            total = len(profile.sentence_lengths)
            profile.short_sentence_pct = short / total
            profile.medium_sentence_pct = medium / total
            profile.long_sentence_pct = long / total

        # Paragraphs
        paragraphs = [p.strip() for p in prose.split("\n\n") if p.strip()]
        profile.paragraph_count = len(paragraphs)
        profile.paragraph_lengths = [len(p.split()) for p in paragraphs]
        if profile.paragraph_lengths:
            profile.avg_paragraph_length = statistics.mean(profile.paragraph_lengths)

        # Dialogue
        dialogue_matches = re.findall(r'["\u201c](.*?)["\u201d]', prose, re.DOTALL)
        profile.dialogue_word_count = sum(len(d.split()) for d in dialogue_matches)
        profile.dialogue_pct = (
            profile.dialogue_word_count / profile.word_count
            if profile.word_count > 0
            else 0.0
        )

        # Punctuation density (per 100 words)
        if profile.word_count > 0:
            scale = 100 / profile.word_count
            profile.comma_density = prose.count(",") * scale
            profile.semicolon_density = prose.count(";") * scale
            profile.dash_density = (prose.count("—") + prose.count("--")) * scale
            profile.question_density = prose.count("?") * scale
            profile.exclamation_density = prose.count("!") * scale

        # Rhythm variation score
        profile.rhythm_variation = self._compute_variation(profile)

        return profile

    def _compute_variation(self, profile: RhythmProfile) -> float:
        """Compute a 0-1 score for how varied the prose rhythm is."""
        if not profile.sentence_lengths or len(profile.sentence_lengths) < 3:
            return 0.5

        # Coefficient of variation for sentence length
        cv = (
            profile.sentence_length_std / profile.avg_sentence_length
            if profile.avg_sentence_length > 0
            else 0
        )
        # Normalize: cv of 0.4-0.6 is ideal
        cv_score = min(1.0, cv / 0.6)

        # Distribution balance: penalize if dominated by one length band
        balance = 1.0 - max(
            profile.short_sentence_pct,
            profile.medium_sentence_pct,
            profile.long_sentence_pct,
        )
        balance_score = balance * 2  # 0.5 max balance → 1.0 score

        # Consecutive length variation: check if adjacent sentences vary
        adjacent_changes = 0
        for i in range(len(profile.sentence_lengths) - 1):
            a, b = profile.sentence_lengths[i], profile.sentence_lengths[i + 1]
            if abs(a - b) > 5:
                adjacent_changes += 1
        adjacency_score = (
            adjacent_changes / (len(profile.sentence_lengths) - 1)
            if len(profile.sentence_lengths) > 1
            else 0.5
        )

        return min(1.0, (cv_score + balance_score + adjacency_score) / 3)

    @staticmethod
    def _split_sentences(prose: str) -> list[str]:
        raw = re.split(r'(?<=[.!?])\s+', prose)
        return [s.strip() for s in raw if s.strip()]
