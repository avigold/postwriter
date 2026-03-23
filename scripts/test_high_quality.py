"""Test a single scene through the full high-quality pipeline.

Exercises all 10 soft critics, 3 branches, and repair loop.
Run with: uv run python scripts/test_high_quality.py
"""

import asyncio
import time
import uuid
from pathlib import Path

from postwriter.config import get_settings
from postwriter.db.session import get_engine, get_session_factory
from postwriter.llm.client import LLMClient
from postwriter.logging_config import setup_logging
from postwriter.orchestrator.scene_loop import SceneLoop
from postwriter.orchestrator.policies import ScenePolicy
from postwriter.profiles import apply_profile
from postwriter.types import AgentContext


async def main():
    setup_logging(log_dir=Path("logs"), console_level=10)  # DEBUG on console

    settings = get_settings()
    apply_profile("high_quality", settings.orchestrator, settings.llm)

    print(f"Policy: {settings.orchestrator.default_branch_count} branches, "
          f"{settings.orchestrator.max_repair_rounds} repair rounds")

    engine = get_engine(settings)
    factory = get_session_factory(engine)

    # Use a scene from the existing manuscript
    mid = uuid.UUID("cb65630f-0186-4921-9e5b-cc21cc7d6750")

    async with factory() as session:
        llm = LLMClient(settings.llm)
        try:
            # Get a scene to test with
            from postwriter.canon.store import CanonStore
            from postwriter.canon.slicer import CanonSlicer

            store = CanonStore(session)
            chapters = await store.get_all_chapters(mid)
            if not chapters:
                print("No chapters found")
                return

            # Use the first scene of the second chapter (skip the opening)
            ch = chapters[1] if len(chapters) > 1 else chapters[0]
            scenes = await store.get_scenes(ch.id)
            if not scenes:
                print("No scenes found")
                return

            scene = scenes[0]
            print(f"Testing scene: {scene.id}")
            print(f"  Purpose: {scene.purpose}")
            print(f"  Pivotal: {scene.is_pivotal}")
            print()

            # Build context
            slicer = CanonSlicer(session, settings.orchestrator)
            context = await slicer.build_scene_context(mid, scene.id)

            # Create the scene loop with high-quality policy
            policy = ScenePolicy.from_settings(settings.orchestrator)
            print(f"Scene policy: {policy.branch_count} branches, "
                  f"{policy.max_repair_rounds} max repair rounds")
            print()

            loop = SceneLoop(session, llm, policy=policy)

            # Run it
            t0 = time.monotonic()
            result = await loop.process_scene(
                manuscript_id=mid,
                scene_id=scene.id,
                context=context,
                is_pivotal=scene.is_pivotal,
            )
            dt = int(time.monotonic() - t0)

            if result:
                print(f"\nResult: {result.label}")
                print(f"  Words: {result.word_count}")
                print(f"  Score: {result.scores.composite if result.scores else 'N/A'}")
                print(f"  Hard pass: {result.hard_pass}")
                print(f"  Time: {dt}s")
                print(f"\nFirst 500 chars:")
                print(result.prose[:500])
            else:
                print("Scene processing failed")

            # Print token usage
            print(f"\nToken usage: {llm.budget.summary()}")

        finally:
            await llm.close()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
