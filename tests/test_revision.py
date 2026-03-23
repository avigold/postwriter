"""Tests for global revision audit passes and backward propagation."""

import pytest

from postwriter.revision.arc_audit import ArcAudit
from postwriter.revision.backward_propagation import BackwardPropagationPlanner
from postwriter.revision.base import RevisionProposal
from postwriter.revision.device_ecology import DeviceEcologyAudit
from postwriter.revision.promise_audit import PromiseAudit
from postwriter.revision.rhythm_audit import RhythmAudit
from postwriter.revision.theme_overstatement import ThemeOverstatementAudit


class TestPromiseAudit:
    @pytest.mark.asyncio
    async def test_detects_unresolved_high_salience(self):
        audit = PromiseAudit()
        data = {
            "promises": [
                {"id": "p1", "description": "The locked box", "status": "open", "salience": 0.9},
                {"id": "p2", "description": "Minor detail", "status": "open", "salience": 0.3},
            ],
        }
        proposals = await audit.audit(data)
        # Only high-salience should trigger
        assert len(proposals) == 1
        assert "locked box" in proposals[0].description

    @pytest.mark.asyncio
    async def test_detects_overdue(self):
        audit = PromiseAudit()
        data = {
            "promises": [
                {"id": "p1", "description": "Overdue promise", "status": "overdue", "salience": 0.8},
            ],
        }
        proposals = await audit.audit(data)
        assert len(proposals) == 1
        assert proposals[0].requires_human_approval

    @pytest.mark.asyncio
    async def test_detects_weak_payoff(self):
        audit = PromiseAudit()
        data = {
            "promises": [
                {
                    "id": "p1", "description": "Important promise",
                    "status": "resolved", "salience": 0.8,
                    "payoff_strength": 0.2, "resolution_scene_id": "s10",
                },
            ],
        }
        proposals = await audit.audit(data)
        assert len(proposals) == 1
        assert "weak payoff" in proposals[0].description.lower()

    @pytest.mark.asyncio
    async def test_no_issues(self):
        audit = PromiseAudit()
        data = {
            "promises": [
                {"id": "p1", "description": "Resolved", "status": "resolved", "salience": 0.7, "payoff_strength": 0.8},
            ],
        }
        proposals = await audit.audit(data)
        assert len(proposals) == 0


class TestArcAudit:
    @pytest.mark.asyncio
    async def test_detects_emotional_jump(self):
        audit = ArcAudit()
        data = {
            "characters": [{"id": "c1", "name": "Elena", "arc_hypotheses": {}}],
            "scene_states": {
                "c1": [
                    {"scene_id": "s1", "emotional_state": {"mood": "happy", "level": "content"}},
                    {"scene_id": "s2", "emotional_state": {"mood": "rage", "level": "fury"}},
                ],
            },
        }
        proposals = await audit.audit(data)
        assert len(proposals) >= 1
        assert "emotional jump" in proposals[0].description.lower()

    @pytest.mark.asyncio
    async def test_no_jump_similar_emotions(self):
        audit = ArcAudit()
        data = {
            "characters": [{"id": "c1", "name": "Elena", "arc_hypotheses": {}}],
            "scene_states": {
                "c1": [
                    {"scene_id": "s1", "emotional_state": {"mood": "uneasy"}},
                    {"scene_id": "s2", "emotional_state": {"mood": "tense"}},
                ],
            },
        }
        proposals = await audit.audit(data)
        assert len(proposals) == 0


class TestDeviceEcologyAudit:
    @pytest.mark.asyncio
    async def test_detects_narrator_tic(self):
        audit = DeviceEcologyAudit()
        # Create data where metaphor appears in almost every chapter
        chapters = {}
        for i in range(10):
            chapters[f"ch{i}"] = {
                "instances": [
                    {"device_type": "metaphor", "span_start": 100},
                    {"device_type": "metaphor", "span_start": 300},
                    {"device_type": "metaphor", "span_start": 500},
                ],
                "word_count": 2000,
            }
        data = {"chapter_devices": chapters}
        proposals = await audit.audit(data)
        assert any("tic" in p.description.lower() or "metaphor" in p.description for p in proposals)

    @pytest.mark.asyncio
    async def test_no_tics_with_variety(self):
        audit = DeviceEcologyAudit()
        chapters = {
            "ch1": {"instances": [{"device_type": "metaphor", "span_start": 100}], "word_count": 2000},
            "ch2": {"instances": [{"device_type": "simile", "span_start": 100}], "word_count": 2000},
            "ch3": {"instances": [{"device_type": "anaphora", "span_start": 100}], "word_count": 2000},
        }
        data = {"chapter_devices": chapters}
        proposals = await audit.audit(data)
        # Should have no narrator tic alerts
        tic_proposals = [p for p in proposals if "tic" in p.description.lower()]
        assert len(tic_proposals) == 0


class TestRhythmAudit:
    @pytest.mark.asyncio
    async def test_detects_sentence_monotony(self):
        audit = RhythmAudit()
        # All chapters have nearly identical avg sentence length
        data = {
            "chapter_rhythms": [
                {"chapter_id": f"ch{i}", "avg_sentence_length": 15.0 + (i * 0.1), "dialogue_pct": 0.3, "rhythm_variation": 0.5}
                for i in range(8)
            ],
        }
        proposals = await audit.audit(data)
        assert any("monotony" in p.description.lower() or "sentence length" in p.description.lower() for p in proposals)

    @pytest.mark.asyncio
    async def test_detects_low_variation(self):
        audit = RhythmAudit()
        data = {
            "chapter_rhythms": [
                {"chapter_id": f"ch{i}", "avg_sentence_length": 12 + i * 3, "dialogue_pct": 0.2 + i * 0.05, "rhythm_variation": 0.2}
                for i in range(6)
            ],
        }
        proposals = await audit.audit(data)
        assert any("variation" in p.description.lower() for p in proposals)

    @pytest.mark.asyncio
    async def test_no_issues_with_variety(self):
        audit = RhythmAudit()
        data = {
            "chapter_rhythms": [
                {"chapter_id": "ch1", "avg_sentence_length": 8, "dialogue_pct": 0.5, "rhythm_variation": 0.7},
                {"chapter_id": "ch2", "avg_sentence_length": 18, "dialogue_pct": 0.2, "rhythm_variation": 0.8},
                {"chapter_id": "ch3", "avg_sentence_length": 12, "dialogue_pct": 0.35, "rhythm_variation": 0.6},
                {"chapter_id": "ch4", "avg_sentence_length": 22, "dialogue_pct": 0.1, "rhythm_variation": 0.7},
            ],
        }
        proposals = await audit.audit(data)
        # Should have no monotony alerts
        monotony = [p for p in proposals if "monotony" in p.description.lower() or "stagnation" in p.description.lower()]
        assert len(monotony) == 0


class TestThemeOverstatement:
    @pytest.mark.asyncio
    async def test_detects_explicit_themes(self):
        audit = ThemeOverstatementAudit()
        data = {
            "themes": [{"id": "t1", "name": "Isolation", "overstatement_risk": 0.5}],
            "theme_manifestations": {
                "t1": [
                    {"scene_id": f"s{i}", "explicitness": 0.8, "mode": "narrated"}
                    for i in range(4)
                ],
            },
        }
        proposals = await audit.audit(data)
        assert any("isolation" in p.description.lower() for p in proposals)

    @pytest.mark.asyncio
    async def test_no_issues_with_subtle_themes(self):
        audit = ThemeOverstatementAudit()
        data = {
            "themes": [{"id": "t1", "name": "Isolation", "overstatement_risk": 0.2}],
            "theme_manifestations": {
                "t1": [
                    {"scene_id": f"s{i}", "explicitness": 0.3, "mode": "situational"}
                    for i in range(4)
                ],
            },
        }
        proposals = await audit.audit(data)
        assert len(proposals) == 0


class TestBackwardPropagation:
    @pytest.mark.asyncio
    async def test_plans_payoff_strengthening(self):
        planner = BackwardPropagationPlanner()
        proposals = [
            RevisionProposal(
                audit_name="promise_audit",
                severity=0.7,
                description="Weak payoff for: the locked box",
                target_scene_ids=["s10"],
                proposed_action="Strengthen payoff",
            ),
        ]
        data = {"scene_order": [f"s{i}" for i in range(15)]}

        tasks = await planner.plan(proposals, data)
        assert len(tasks) >= 1
        # Should target scenes before s10
        for t in tasks:
            assert t.target_scene_id != "s10"  # Should seed earlier
            assert "preparation" in t.instruction.lower() or "seed" in t.instruction.lower() or "plant" in t.instruction.lower()

    @pytest.mark.asyncio
    async def test_plans_emotional_bridging(self):
        planner = BackwardPropagationPlanner()
        proposals = [
            RevisionProposal(
                audit_name="arc_audit",
                severity=0.6,
                description="Elena: emotional jump from happy to rage",
                target_scene_ids=["s3", "s7"],
                evidence={"from": "happy", "to": "rage"},
            ),
        ]
        data = {"scene_order": [f"s{i}" for i in range(10)]}

        tasks = await planner.plan(proposals, data)
        assert len(tasks) >= 1
        # Should target a scene between s3 and s7
        target_idx = int(tasks[0].target_scene_id[1:])
        assert 3 < target_idx < 7

    @pytest.mark.asyncio
    async def test_skips_low_severity(self):
        planner = BackwardPropagationPlanner()
        proposals = [
            RevisionProposal(
                audit_name="rhythm_audit",
                severity=0.3,
                description="Minor rhythm issue",
            ),
        ]
        data = {"scene_order": [f"s{i}" for i in range(10)]}

        tasks = await planner.plan(proposals, data)
        assert len(tasks) == 0

    @pytest.mark.asyncio
    async def test_orders_tasks_reverse_chronological(self):
        planner = BackwardPropagationPlanner()
        proposals = [
            RevisionProposal(
                audit_name="promise_audit", severity=0.7,
                description="Weak payoff", target_scene_ids=["s12"],
            ),
        ]
        data = {"scene_order": [f"s{i}" for i in range(15)]}

        tasks = await planner.plan(proposals, data)
        if len(tasks) > 1:
            # Later scenes should be modified first (reverse chronological)
            ordinals = [int(t.target_scene_id[1:]) for t in tasks]
            assert ordinals == sorted(ordinals, reverse=True)
