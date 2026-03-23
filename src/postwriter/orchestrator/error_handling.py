"""Error recovery strategies for the orchestrator."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, TypeVar

from postwriter.errors import BudgetExhausted, LLMError

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def with_retry(
    fn: Callable[..., Any],
    *args: Any,
    max_retries: int = 3,
    backoff_base: float = 2.0,
    fallback: Any = None,
    **kwargs: Any,
) -> Any:
    """Execute an async function with retries and exponential backoff."""
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            return await fn(*args, **kwargs)
        except BudgetExhausted:
            raise  # Don't retry budget exhaustion
        except LLMError as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = backoff_base ** attempt
                logger.warning(
                    "LLM error (attempt %d/%d): %s. Retrying in %.1fs",
                    attempt + 1, max_retries, e, wait,
                )
                await asyncio.sleep(wait)
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = backoff_base ** attempt
                logger.warning(
                    "Error (attempt %d/%d): %s. Retrying in %.1fs",
                    attempt + 1, max_retries, e, wait,
                )
                await asyncio.sleep(wait)

    if fallback is not None:
        logger.warning("All retries exhausted, using fallback")
        return fallback

    if last_error:
        raise last_error
    return None


async def graceful_degradation(
    primary_fn: Callable[..., Any],
    fallback_fn: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Try the primary function, fall back to a simpler alternative on failure."""
    try:
        return await primary_fn(*args, **kwargs)
    except (LLMError, BudgetExhausted) as e:
        logger.warning("Primary function failed (%s), falling back", e)
        return await fallback_fn(*args, **kwargs)
