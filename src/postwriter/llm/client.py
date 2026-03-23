"""Anthropic SDK wrapper with model tier routing, retries, and rate limiting."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import anthropic
import httpx

from postwriter.config import LLMSettings
from postwriter.errors import LLMError
from postwriter.llm.budget import TokenBudget
from postwriter.types import ModelTier

logger = logging.getLogger(__name__)

# Default retry config
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2.0


class LLMClient:
    """Async wrapper around the Anthropic API with tier routing and budgets."""

    def __init__(self, settings: LLMSettings, budget: TokenBudget | None = None) -> None:
        self.settings = settings
        self.budget = budget or TokenBudget()
        self._client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key,
            timeout=httpx.Timeout(connect=10.0, read=600.0, write=600.0, pool=600.0),
        )

        # Model ID mapping
        self._model_map: dict[ModelTier, str] = {
            ModelTier.OPUS: settings.opus_model,
            ModelTier.SONNET: settings.sonnet_model,
            ModelTier.HAIKU: settings.haiku_model,
        }

        # Rate-limiting semaphores per tier
        self._semaphores: dict[ModelTier, asyncio.Semaphore] = {
            ModelTier.OPUS: asyncio.Semaphore(settings.max_concurrent_opus),
            ModelTier.SONNET: asyncio.Semaphore(settings.max_concurrent_sonnet),
            ModelTier.HAIKU: asyncio.Semaphore(settings.max_concurrent_haiku),
        }

    def _get_model_id(self, tier: ModelTier) -> str:
        return self._model_map[tier]

    async def complete(
        self,
        tier: ModelTier,
        messages: list[dict[str, Any]],
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: dict[str, Any] | None = None,
    ) -> LLMResponse:
        """Send a completion request to the Anthropic API with tier-based routing."""
        self.budget.check(tier)

        model_id = self._get_model_id(tier)
        sem = self._semaphores[tier]

        kwargs: dict[str, Any] = {
            "model": model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice

        import time

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                t0 = time.monotonic()
                async with sem:
                    response = await self._client.messages.create(**kwargs)
                duration_ms = int((time.monotonic() - t0) * 1000)

                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                self.budget.record(tier, input_tokens, output_tokens)

                logger.info(
                    "LLM call completed: %s %d+%d tokens (%dms)",
                    tier.value, input_tokens, output_tokens, duration_ms,
                    extra={
                        "model_tier": tier.value,
                        "tokens_in": input_tokens,
                        "tokens_out": output_tokens,
                        "duration_ms": duration_ms,
                    },
                )

                # Extract text content
                text = ""
                tool_use_blocks: list[dict[str, Any]] = []
                for block in response.content:
                    if block.type == "text":
                        text += block.text
                    elif block.type == "tool_use":
                        tool_use_blocks.append({
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        })

                return LLMResponse(
                    text=text,
                    tool_use=tool_use_blocks,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model=model_id,
                    stop_reason=response.stop_reason,
                )

            except anthropic.RateLimitError:
                wait = RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    "Rate limited on %s (attempt %d/%d), waiting %.1fs",
                    tier.value, attempt + 1, MAX_RETRIES, wait,
                )
                last_error = anthropic.RateLimitError(
                    message="Rate limited",
                    response=None,  # type: ignore[arg-type]
                    body=None,
                )
                await asyncio.sleep(wait)

            except anthropic.APIError as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_BACKOFF_BASE ** attempt
                    logger.warning(
                        "API error on %s (attempt %d/%d): %s",
                        tier.value, attempt + 1, MAX_RETRIES, e,
                    )
                    await asyncio.sleep(wait)

            except (TimeoutError, asyncio.TimeoutError, OSError) as e:
                last_error = e  # type: ignore[assignment]
                wait = RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    "Connection error on %s (attempt %d/%d): %s",
                    tier.value, attempt + 1, MAX_RETRIES, e,
                )
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(wait)

        raise LLMError(tier.value, str(last_error))

    async def close(self) -> None:
        await self._client.close()


class LLMResponse:
    """Structured response from an LLM call."""

    __slots__ = ("text", "tool_use", "input_tokens", "output_tokens", "model", "stop_reason")

    def __init__(
        self,
        text: str,
        tool_use: list[dict[str, Any]],
        input_tokens: int,
        output_tokens: int,
        model: str,
        stop_reason: str | None,
    ) -> None:
        self.text = text
        self.tool_use = tool_use
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.model = model
        self.stop_reason = stop_reason
