"""Rule-based detectors for lexical and syntactic devices."""

from __future__ import annotations

import re
from collections import Counter

from postwriter.devices.taxonomy import DeviceInstance
from postwriter.types import DeviceType


class LexicalDetector:
    """Detects lexical/syntactic devices using regex and heuristics."""

    def detect_all(self, prose: str) -> list[DeviceInstance]:
        """Run all rule-based detectors on the prose."""
        instances: list[DeviceInstance] = []
        instances.extend(self.detect_alliteration(prose))
        instances.extend(self.detect_anaphora(prose))
        instances.extend(self.detect_epistrophe(prose))
        instances.extend(self.detect_rhetorical_questions(prose))
        instances.extend(self.detect_triadic_constructions(prose))
        instances.extend(self.detect_sentence_fragments(prose))
        instances.extend(self.detect_polysyndeton(prose))
        instances.extend(self.detect_asyndeton(prose))
        return instances

    def detect_alliteration(self, prose: str) -> list[DeviceInstance]:
        """Detect alliteration: 3+ words starting with the same consonant sound in proximity."""
        instances = []
        sentences = _split_sentences(prose)
        for sent in sentences:
            words = re.findall(r"\b[a-zA-Z]+\b", sent)
            if len(words) < 3:
                continue

            for i in range(len(words) - 2):
                window = words[i:i + 4]  # check windows of 3-4 words
                initials = [w[0].lower() for w in window if w[0].lower() not in "aeiou"]
                if len(initials) >= 3:
                    counts = Counter(initials)
                    for letter, count in counts.items():
                        if count >= 3:
                            matched = [w for w in window if w[0].lower() == letter]
                            text = " ".join(matched)
                            start = prose.find(matched[0], prose.find(sent))
                            if start >= 0:
                                instances.append(DeviceInstance(
                                    device_type=DeviceType.ALLITERATION,
                                    span_start=start,
                                    span_end=start + len(text),
                                    text=text,
                                    confidence=0.6,
                                    metadata={"letter": letter, "count": count},
                                ))
                            break
        return instances

    def detect_anaphora(self, prose: str) -> list[DeviceInstance]:
        """Detect anaphora: consecutive sentences/clauses starting with the same words."""
        instances = []
        sentences = _split_sentences(prose)

        for i in range(len(sentences) - 1):
            words_a = sentences[i].split()[:3]
            words_b = sentences[i + 1].split()[:3]
            if not words_a or not words_b:
                continue

            # Check 1-3 word overlap at start
            for length in range(min(3, len(words_a), len(words_b)), 0, -1):
                if [w.lower() for w in words_a[:length]] == [w.lower() for w in words_b[:length]]:
                    repeated = " ".join(words_a[:length])
                    start = prose.find(sentences[i])
                    end = prose.find(sentences[i + 1]) + len(sentences[i + 1])
                    if start >= 0:
                        instances.append(DeviceInstance(
                            device_type=DeviceType.ANAPHORA,
                            span_start=start,
                            span_end=end,
                            text=f"{sentences[i][:80]}... / {sentences[i+1][:80]}...",
                            confidence=0.7,
                            metadata={"repeated_opening": repeated},
                        ))
                    break
        return instances

    def detect_epistrophe(self, prose: str) -> list[DeviceInstance]:
        """Detect epistrophe: consecutive sentences ending with the same word(s)."""
        instances = []
        sentences = _split_sentences(prose)

        for i in range(len(sentences) - 1):
            words_a = sentences[i].rstrip(".!?,:;").split()[-2:]
            words_b = sentences[i + 1].rstrip(".!?,:;").split()[-2:]
            if not words_a or not words_b:
                continue

            if words_a[-1].lower() == words_b[-1].lower() and len(words_a[-1]) > 2:
                start = prose.find(sentences[i])
                end = prose.find(sentences[i + 1]) + len(sentences[i + 1])
                if start >= 0:
                    instances.append(DeviceInstance(
                        device_type=DeviceType.EPISTROPHE,
                        span_start=start,
                        span_end=end,
                        text=f"...{words_a[-1]} / ...{words_b[-1]}",
                        confidence=0.6,
                        metadata={"repeated_ending": words_a[-1]},
                    ))
        return instances

    def detect_rhetorical_questions(self, prose: str) -> list[DeviceInstance]:
        """Detect rhetorical questions in narration (not dialogue)."""
        instances = []
        # Find question marks outside of dialogue
        # Simple heuristic: questions not preceded by a dialogue tag
        lines = prose.split("\n")
        for line in lines:
            # Skip dialogue lines (starting with quotes or containing speech tags)
            stripped = line.strip()
            if stripped.startswith('"') or stripped.startswith("'") or stripped.startswith("\u201c"):
                continue

            questions = re.finditer(r'[^""\u201c\u201d]*\?', line)
            for m in questions:
                text = m.group().strip()
                if len(text) > 5 and not re.search(r'(said|asked|wondered|inquired)', text, re.I):
                    start = prose.find(text)
                    if start >= 0:
                        instances.append(DeviceInstance(
                            device_type=DeviceType.RHETORICAL_QUESTION,
                            span_start=start,
                            span_end=start + len(text),
                            text=text[:100],
                            confidence=0.5,  # Lower confidence — needs context
                        ))
        return instances

    def detect_triadic_constructions(self, prose: str) -> list[DeviceInstance]:
        """Detect triadic (rule of three) constructions: X, Y, and Z patterns."""
        instances = []
        # Pattern: word, word, and word  or  word, word, word
        pattern = r"\b(\w+(?:\s+\w+)?),\s+(\w+(?:\s+\w+)?),\s+(?:and\s+)?(\w+(?:\s+\w+)?)\b"
        for m in re.finditer(pattern, prose):
            instances.append(DeviceInstance(
                device_type=DeviceType.TRIADIC_CONSTRUCTION,
                span_start=m.start(),
                span_end=m.end(),
                text=m.group(),
                confidence=0.6,
            ))
        return instances

    def detect_sentence_fragments(self, prose: str) -> list[DeviceInstance]:
        """Detect sentence fragments: very short 'sentences' that lack a main verb."""
        instances = []
        sentences = _split_sentences(prose)
        for sent in sentences:
            words = sent.split()
            # Fragment heuristic: 1-4 words, ends with period, no common verb forms
            if 1 <= len(words) <= 4:
                # Check for common verb indicators
                has_verb = bool(re.search(
                    r"\b(was|were|is|are|had|has|have|did|do|does|went|came|said|"
                    r"looked|felt|knew|thought|saw|heard|made|took|got|let|ran|"
                    r"\w+ed|'\w+)\b",
                    sent, re.I,
                ))
                if not has_verb:
                    start = prose.find(sent)
                    if start >= 0:
                        instances.append(DeviceInstance(
                            device_type=DeviceType.SENTENCE_FRAGMENT,
                            span_start=start,
                            span_end=start + len(sent),
                            text=sent,
                            confidence=0.5,
                        ))
        return instances

    def detect_polysyndeton(self, prose: str) -> list[DeviceInstance]:
        """Detect polysyndeton: repeated conjunctions (and...and...and)."""
        instances = []
        # Look for 3+ 'and' in close proximity
        for m in re.finditer(r"(\band\b[^.!?]{1,40}){2,}\band\b", prose, re.I):
            instances.append(DeviceInstance(
                device_type=DeviceType.POLYSYNDETON,
                span_start=m.start(),
                span_end=m.end(),
                text=m.group()[:100],
                confidence=0.6,
            ))
        return instances

    def detect_asyndeton(self, prose: str) -> list[DeviceInstance]:
        """Detect asyndeton: list without conjunctions (X, Y, Z with no 'and')."""
        instances = []
        # Pattern: 3+ comma-separated items without 'and' before the last
        pattern = r"(\b\w+,\s+){2,}\w+[^,\s]"
        for m in re.finditer(pattern, prose):
            text = m.group()
            # Check no 'and' before the last item
            if " and " not in text.split(",")[-1]:
                instances.append(DeviceInstance(
                    device_type=DeviceType.ASYNDETON,
                    span_start=m.start(),
                    span_end=m.end(),
                    text=text[:100],
                    confidence=0.5,
                ))
        return instances


def _split_sentences(prose: str) -> list[str]:
    """Split prose into sentences. Simple heuristic."""
    # Split on sentence-ending punctuation followed by space or newline
    raw = re.split(r'(?<=[.!?])\s+', prose)
    return [s.strip() for s in raw if s.strip()]
