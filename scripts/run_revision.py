"""Run global revision on an existing manuscript.

Usage: uv run python scripts/run_revision.py [manuscript-id]

If no ID given, reads from .postwriter file.
"""

import asyncio
import json
import sys
import uuid
from pathlib import Path

from postwriter.config import get_settings
from postwriter.db.session import get_engine, get_session_factory
from postwriter.llm.client import LLMClient
from postwriter.logging_config import setup_logging
from postwriter.orchestrator.global_revision import GlobalRevisionOrchestrator


async def main():
    setup_logging(log_dir=Path("logs"))
    settings = get_settings()

    # Get manuscript ID
    if len(sys.argv) > 1:
        mid = uuid.UUID(sys.argv[1])
    else:
        pw_file = Path(".postwriter")
        if pw_file.exists():
            data = json.loads(pw_file.read_text())
            mid = uuid.UUID(data["manuscript_id"])
            print(f"Using manuscript from .postwriter: {data.get('title', mid)}")
        else:
            print("Usage: uv run python scripts/run_revision.py [manuscript-id]")
            print("Or run from a directory with a .postwriter file.")
            sys.exit(1)

    engine = get_engine(settings)
    factory = get_session_factory(engine)

    async with factory() as session:
        llm = LLMClient(settings.llm)
        try:
            reviser = GlobalRevisionOrchestrator(session, llm)
            proposals = await reviser.run(mid)
            print(f"\nDone: {len(proposals)} proposals processed")
        finally:
            await llm.close()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
