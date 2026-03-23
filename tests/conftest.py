"""Shared fixtures for the postwriter test suite."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from postwriter.config import LLMSettings, OrchestratorSettings
from postwriter.llm.budget import TokenBudget
from postwriter.llm.client import LLMClient, LLMResponse
from postwriter.models.base import Base
from postwriter.prompts.loader import PromptLoader

TEST_DB_URL = "postgresql+asyncpg://postwriter:postwriter@localhost:5450/postwriter"


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(TEST_DB_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess
        await sess.rollback()


@pytest.fixture
def prompt_loader() -> PromptLoader:
    return PromptLoader()


@pytest.fixture
def mock_llm_response() -> LLMResponse:
    return LLMResponse(
        text='{"result": "test"}',
        tool_use=[],
        input_tokens=100,
        output_tokens=50,
        model="claude-sonnet-4-6",
        stop_reason="end_turn",
    )


@pytest.fixture
def mock_llm_client(mock_llm_response) -> LLMClient:
    """A mock LLM client that returns a canned response."""
    client = MagicMock(spec=LLMClient)
    client.complete = AsyncMock(return_value=mock_llm_response)
    client.budget = TokenBudget()
    client.settings = LLMSettings(anthropic_api_key="test-key")
    return client


@pytest.fixture
def token_budget() -> TokenBudget:
    return TokenBudget()


@pytest.fixture
def orchestrator_settings() -> OrchestratorSettings:
    return OrchestratorSettings()
