"""Tests for rule-based device detectors and rhythm analysis."""

import pytest

from postwriter.devices.detectors.lexical import LexicalDetector
from postwriter.devices.detectors.rhythm import RhythmAnalyzer
from postwriter.devices.imagery_domains import ImageryDomainClassifier
from postwriter.devices.taxonomy import DeviceInstance
from postwriter.types import DeviceType


class TestLexicalDetector:
    def setup_method(self):
        self.detector = LexicalDetector()

    def test_detect_alliteration(self):
        prose = "Peter picked a peck of pickled peppers by the pier."
        instances = self.detector.detect_alliteration(prose)
        assert len(instances) >= 1
        assert instances[0].device_type == DeviceType.ALLITERATION

    def test_detect_anaphora(self):
        prose = (
            "She walked to the door. She walked to the window. "
            "She walked to the mirror and stopped."
        )
        instances = self.detector.detect_anaphora(prose)
        assert len(instances) >= 1
        assert instances[0].device_type == DeviceType.ANAPHORA

    def test_detect_rhetorical_questions(self):
        prose = (
            "The harbor was empty. Who could blame them for leaving? "
            "What was there to stay for?"
        )
        instances = self.detector.detect_rhetorical_questions(prose)
        assert len(instances) >= 1
        assert instances[0].device_type == DeviceType.RHETORICAL_QUESTION

    def test_detect_sentence_fragments(self):
        prose = "The door opened. Silence. Nothing but cold air. She stepped inside."
        instances = self.detector.detect_sentence_fragments(prose)
        assert len(instances) >= 1
        # "Silence." and "Nothing but cold air." should be caught
        fragment_texts = [i.text for i in instances]
        assert any("Silence" in t for t in fragment_texts)

    def test_detect_triadic_construction(self):
        prose = "She was tired, hungry, and afraid."
        instances = self.detector.detect_triadic_constructions(prose)
        assert len(instances) >= 1
        assert instances[0].device_type == DeviceType.TRIADIC_CONSTRUCTION

    def test_detect_all(self):
        prose = (
            "Peter picked a peck. Silence. Nothing but wind. "
            "She was cold, tired, and alone. Who could blame her?"
        )
        instances = self.detector.detect_all(prose)
        assert len(instances) >= 2  # At least fragments + triadic or question
        types = {i.device_type for i in instances}
        assert len(types) >= 2  # Multiple device types

    def test_no_false_positives_on_plain_prose(self):
        prose = (
            "Elena walked to the harbor. The water was gray and still. "
            "She watched a fishing boat return to the dock."
        )
        instances = self.detector.detect_all(prose)
        # Should find few or no devices in plain prose
        assert len(instances) <= 2


class TestRhythmAnalyzer:
    def setup_method(self):
        self.analyzer = RhythmAnalyzer()

    def test_basic_analysis(self):
        prose = (
            "The harbor lay flat under a low sky. Elena pulled her coat tighter. "
            "Salt air stung her eyes. She hadn't been here in eleven years, not since "
            "the night she left with nothing but a suitcase and a lie she told herself "
            "was the truth."
        )
        profile = self.analyzer.analyze(prose)
        assert profile.word_count > 0
        assert profile.sentence_count >= 3
        assert profile.avg_sentence_length > 0
        assert 0.0 <= profile.short_sentence_pct <= 1.0

    def test_rhythm_variation(self):
        # Mix of short and long sentences should score higher
        varied = (
            "She stopped. The harbor stretched before her, a flat gray expanse of water "
            "that seemed to merge with the sky at some indeterminate point on the horizon. "
            "Silence. Nothing moved. Then a gull screamed overhead and the spell broke and "
            "she walked forward into the wind."
        )
        monotone = (
            "She walked to the door and opened it. She stepped outside into the cold. "
            "She looked at the harbor in the distance. She pulled her coat around her. "
            "She started walking down the path slowly."
        )
        varied_profile = self.analyzer.analyze(varied)
        monotone_profile = self.analyzer.analyze(monotone)
        assert varied_profile.rhythm_variation > monotone_profile.rhythm_variation

    def test_dialogue_detection(self):
        prose = (
            '"Where have you been?" Marcus asked.\n'
            'Elena shrugged. "Away."\n'
            '"That\'s not an answer."\n'
            '"It\'s the only one I have."'
        )
        profile = self.analyzer.analyze(prose)
        assert profile.dialogue_pct > 0.3  # Should be dialogue-heavy

    def test_empty_prose(self):
        profile = self.analyzer.analyze("")
        assert profile.word_count == 0
        assert profile.sentence_count == 0


class TestImageryClassifier:
    def setup_method(self):
        self.classifier = ImageryDomainClassifier()

    def test_classify_water_metaphor(self):
        inst = DeviceInstance(
            device_type=DeviceType.METAPHOR,
            span_start=0, span_end=50,
            text="grief flooded through her like a tide",
        )
        domain = self.classifier.classify_instance(inst)
        assert domain == "water"

    def test_classify_fire_metaphor(self):
        inst = DeviceInstance(
            device_type=DeviceType.SIMILE,
            span_start=0, span_end=50,
            text="anger burned in her chest like an ember",
        )
        domain = self.classifier.classify_instance(inst)
        assert domain == "fire"

    def test_classify_with_preset_domain(self):
        inst = DeviceInstance(
            device_type=DeviceType.METAPHOR,
            span_start=0, span_end=50,
            text="test",
            imagery_domain="architecture",
        )
        domain = self.classifier.classify_instance(inst)
        assert domain == "architecture"

    def test_imagery_profile(self):
        instances = [
            DeviceInstance(DeviceType.METAPHOR, 0, 10, "waves of grief", imagery_domain="water"),
            DeviceInstance(DeviceType.SIMILE, 20, 30, "like a tide", imagery_domain="water"),
            DeviceInstance(DeviceType.METAPHOR, 40, 50, "walls crumbled", imagery_domain="architecture"),
        ]
        profile = self.classifier.profile(instances)
        assert profile.total_figurative == 3
        assert profile.dominant_domain == "water"
        assert profile.domain_diversity > 0  # Two domains = some diversity
        assert profile.concentration_index() > 0
