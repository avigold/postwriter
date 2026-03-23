"""Tests for graph metrics, temporal tracking, and overuse detection."""

from postwriter.devices.overuse_rules import detect_overuse, suggest_underuse
from postwriter.devices.taxonomy import DeviceInstance
from postwriter.graphs.metrics import DeviceMetrics, compute_metrics
from postwriter.graphs.temporal import SceneDeviceData, TemporalGraph
from postwriter.scoring.device_balance import compute_device_balance_score
from postwriter.types import DeviceType


def _make_instances(types_and_positions: list[tuple[DeviceType, int]]) -> list[DeviceInstance]:
    return [
        DeviceInstance(
            device_type=dt,
            span_start=pos,
            span_end=pos + 20,
            text=f"device at {pos}",
        )
        for dt, pos in types_and_positions
    ]


class TestComputeMetrics:
    def test_empty(self):
        m = compute_metrics([], 0)
        assert m.total_instances == 0
        assert m.density_per_1000 == 0.0

    def test_basic_metrics(self):
        instances = _make_instances([
            (DeviceType.METAPHOR, 100),
            (DeviceType.METAPHOR, 500),
            (DeviceType.SIMILE, 300),
            (DeviceType.ANAPHORA, 700),
        ])
        m = compute_metrics(instances, 1000)

        assert m.total_instances == 4
        assert m.density_per_1000 == 4.0
        assert m.type_counts["metaphor"] == 2
        assert m.type_counts["simile"] == 1

    def test_burstiness_spread(self):
        # Evenly spread devices should have low burstiness
        instances = _make_instances([
            (DeviceType.METAPHOR, 0),
            (DeviceType.METAPHOR, 1000),
            (DeviceType.METAPHOR, 2000),
            (DeviceType.METAPHOR, 3000),
        ])
        m = compute_metrics(instances, 4000)
        assert m.burstiness.get("metaphor", 0) < 0.6  # Not very bursty

    def test_functional_diversity(self):
        instances = [
            DeviceInstance(DeviceType.METAPHOR, 0, 20, "text", estimated_function="tension"),
            DeviceInstance(DeviceType.METAPHOR, 100, 120, "text", estimated_function="tension"),
            DeviceInstance(DeviceType.SIMILE, 200, 220, "text", estimated_function="beauty"),
        ]
        m = compute_metrics(instances, 500)
        assert m.functional_diversity > 0

    def test_character_concentration(self):
        instances = [
            DeviceInstance(DeviceType.METAPHOR, 0, 20, "text", speaker_character="Elena"),
            DeviceInstance(DeviceType.SIMILE, 100, 120, "text", speaker_character="Elena"),
            DeviceInstance(DeviceType.IRONY, 200, 220, "text", speaker_character="Marcus"),
        ]
        m = compute_metrics(instances, 500)
        assert m.character_concentration > 0.5  # Elena dominates

    def test_imagery_concentration(self):
        instances = [
            DeviceInstance(DeviceType.METAPHOR, 0, 20, "text", imagery_domain="water"),
            DeviceInstance(DeviceType.METAPHOR, 100, 120, "text", imagery_domain="water"),
            DeviceInstance(DeviceType.SIMILE, 200, 220, "text", imagery_domain="water"),
        ]
        m = compute_metrics(instances, 500)
        assert m.imagery_concentration == 1.0  # Complete monoculture


class TestTemporalGraph:
    def test_add_and_query(self):
        graph = TemporalGraph()
        graph.add_scene(SceneDeviceData(
            scene_id="s1", chapter_id="c1",
            scene_ordinal=1, chapter_ordinal=1,
            word_count=800,
            instances=_make_instances([(DeviceType.METAPHOR, 100), (DeviceType.SIMILE, 200)]),
        ))
        graph.add_scene(SceneDeviceData(
            scene_id="s2", chapter_id="c1",
            scene_ordinal=2, chapter_ordinal=1,
            word_count=600,
            instances=_make_instances([(DeviceType.METAPHOR, 100)]),
        ))

        assert graph.scene_count == 2
        freq = graph.device_frequency_over_time(DeviceType.METAPHOR)
        assert freq == [(1, 1), (2, 1)]

    def test_chapter_summary(self):
        graph = TemporalGraph()
        graph.add_scene(SceneDeviceData(
            scene_id="s1", chapter_id="c1",
            scene_ordinal=1, chapter_ordinal=1,
            word_count=1000,
            instances=_make_instances([
                (DeviceType.METAPHOR, 100),
                (DeviceType.METAPHOR, 200),
                (DeviceType.SIMILE, 300),
            ]),
        ))

        summary = graph.chapter_summary()
        assert len(summary) == 1
        assert summary[0]["total_devices"] == 3
        assert summary[0]["density_per_1000"] == 3.0


class TestOveruseDetection:
    def test_no_overuse(self):
        m = DeviceMetrics(
            total_instances=3, total_words=1000,
            type_counts={"metaphor": 1, "simile": 1, "anaphora": 1},
            burstiness={"metaphor": 0.3},
            max_local_density=5.0,
            same_function_same_device=0,
            imagery_concentration=0.3,
        )
        alerts = detect_overuse(m)
        assert len(alerts) == 0

    def test_recurrence_cap_exceeded(self):
        m = DeviceMetrics(
            total_instances=5, total_words=1000,
            type_counts={"rhetorical_question": 5},
        )
        alerts = detect_overuse(m, recurrence_caps={"rhetorical_question": 3})
        assert len(alerts) >= 1
        assert any("cap" in a.reason for a in alerts)

    def test_high_burstiness(self):
        m = DeviceMetrics(
            total_instances=4, total_words=1000,
            type_counts={"metaphor": 4},
            burstiness={"metaphor": 0.85},
        )
        alerts = detect_overuse(m)
        assert any("burstiness" in a.reason.lower() for a in alerts)

    def test_imagery_monoculture(self):
        m = DeviceMetrics(
            total_instances=6, total_words=1000,
            type_counts={"metaphor": 6},
            imagery_concentration=0.8,
        )
        alerts = detect_overuse(m)
        assert any("imagery" in a.reason.lower() or "monoculture" in a.reason.lower() for a in alerts)


class TestUnderuseSuggestions:
    def test_concealment_scene(self):
        suggestions = suggest_underuse(
            "Elena conceals her knowledge of the letters",
            "deception and misdirection",
            current_devices=set(),
        )
        types = {s.device_type for s in suggestions}
        assert "subtext_exchange" in types or "evasive_reply" in types

    def test_no_suggestions_for_simple_scene(self):
        suggestions = suggest_underuse(
            "Elena walks to the harbor",
            "internal reluctance",
            current_devices=set(),
        )
        # May or may not have suggestions, but shouldn't error
        assert isinstance(suggestions, list)


class TestDeviceBalanceScore:
    def test_perfect_balance(self):
        m = DeviceMetrics(total_instances=3, total_words=1000)
        score = compute_device_balance_score(m)
        assert score == 1.0

    def test_overuse_penalty(self):
        m = DeviceMetrics(
            total_instances=10, total_words=1000,
            type_counts={"rhetorical_question": 8},
            max_local_density=20.0,
            same_function_same_device=4,
            imagery_concentration=0.9,
        )
        score = compute_device_balance_score(m)
        assert score <= 0.5
