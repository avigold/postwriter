"""Tests for checkpoint data serialization (Redis tests require a running instance)."""

from postwriter.orchestrator.checkpoint import CheckpointData


def test_checkpoint_roundtrip():
    cp = CheckpointData(
        manuscript_id="test-123",
        phase="drafting",
        current_chapter_ordinal=5,
        current_scene_ordinal=12,
        total_words=25000,
        scenes_processed=40,
        token_usage={"opus": {"total": 5000}, "sonnet": {"total": 50000}},
    )

    data = cp.to_dict()
    restored = CheckpointData.from_dict(data)

    assert restored.manuscript_id == "test-123"
    assert restored.phase == "drafting"
    assert restored.current_chapter_ordinal == 5
    assert restored.total_words == 25000
    assert restored.token_usage["opus"]["total"] == 5000


def test_checkpoint_defaults():
    cp = CheckpointData(manuscript_id="m1", phase="planning")
    assert cp.current_chapter_ordinal == 0
    assert cp.scenes_processed == 0
    assert cp.token_usage is None
