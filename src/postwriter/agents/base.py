"""Base agent class with common prompt rendering, LLM calling, and output parsing."""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import BaseModel

from postwriter.errors import ParseError
from postwriter.llm.client import LLMClient, LLMResponse
from postwriter.prompts.loader import PromptLoader
from postwriter.types import AgentContext, AgentResult, ModelTier

logger = logging.getLogger(__name__)

PARSE_RETRY_MAX = 2


class BaseAgent:
    """Base class for all agents in the fiction system.

    Subclasses should set:
        - role: str
        - model_tier: ModelTier
        - template_name: str (the Jinja2 template file)
        - response_model: type[BaseModel] | None (for structured output parsing)

    And optionally override:
        - build_template_context() to customise template variables
        - build_system_prompt() for a custom system message
        - parse_response() for custom response parsing
    """

    role: str = "base"
    model_tier: ModelTier = ModelTier.SONNET
    template_name: str = ""
    response_model: type[BaseModel] | None = None

    def __init__(
        self,
        llm: LLMClient,
        prompts: PromptLoader | None = None,
    ) -> None:
        self._llm = llm
        self._prompts = prompts or PromptLoader()

    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute the agent: render prompt, call LLM, parse response."""
        import time
        t0 = time.monotonic()
        logger.info(
            "Agent %s starting (tier=%s)", self.role, self.model_tier.value,
            extra={"agent_role": self.role, "model_tier": self.model_tier.value,
                   "manuscript_id": context.manuscript_id},
        )
        logger.debug("Agent %s: building prompts...", self.role)
        system = self.build_system_prompt(context)
        user_message = self.build_user_message(context)
        logger.debug(
            "Agent %s: system=%d chars, user=%d chars",
            self.role, len(system), len(user_message),
        )

        messages = [{"role": "user", "content": user_message}]

        # Tools for structured output
        tools = self._build_tools() if self.response_model else None
        tool_choice = (
            {"type": "tool", "name": "respond"}
            if self.response_model
            else None
        )
        logger.debug(
            "Agent %s: tool_use=%s, max_tokens=%d, temp=%.1f",
            self.role, bool(tools), self._max_tokens(), self._temperature(),
        )

        try:
            from postwriter.cli.display import thinking
            logger.debug("Agent %s: entering thinking spinner...", self.role)
            async with thinking(self._thinking_label()):
                logger.debug("Agent %s: calling LLM...", self.role)
                response = await self._llm.complete(
                    tier=self.model_tier,
                    messages=messages,
                    system=system,
                    max_tokens=self._max_tokens(),
                    temperature=self._temperature(),
                    tools=tools,
                    tool_choice=tool_choice,
                )
            logger.debug(
                "Agent %s: LLM returned, stop=%s, text=%d chars, tools=%d blocks",
                self.role, response.stop_reason, len(response.text), len(response.tool_use),
            )

            logger.debug("Agent %s: parsing response...", self.role)
            parsed = self.parse_response(response, context)
            logger.debug("Agent %s: parse succeeded", self.role)

            duration_ms = int((time.monotonic() - t0) * 1000)
            logger.info(
                "Agent %s completed (%dms, %d+%d tokens)",
                self.role, duration_ms, response.input_tokens, response.output_tokens,
                extra={"agent_role": self.role, "duration_ms": duration_ms,
                       "tokens_in": response.input_tokens, "tokens_out": response.output_tokens},
            )

            return AgentResult(
                success=True,
                agent_role=self.role,
                model_tier=self.model_tier,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                raw_response=response.text,
                parsed=parsed,
            )

        except ParseError as e:
            logger.error("Parse error in %s: %s", self.role, e,
                         extra={"agent_role": self.role})
            return AgentResult(
                success=False,
                agent_role=self.role,
                model_tier=self.model_tier,
                error=str(e),
            )
        except Exception as e:
            logger.error("Agent %s failed: %s", self.role, e)
            return AgentResult(
                success=False,
                agent_role=self.role,
                model_tier=self.model_tier,
                error=str(e),
            )

    def build_system_prompt(self, context: AgentContext) -> str:
        """Build the system prompt. Override for custom system messages."""
        return (
            f"You are a specialized {self.role} agent in a fiction orchestration system. "
            "Follow instructions precisely. Respond only with the requested format."
        )

    def build_user_message(self, context: AgentContext) -> str:
        """Build the user message from the template and context."""
        if self.template_name and self._prompts.has_template(self.template_name):
            template_vars = self.build_template_context(context)
            return self._prompts.render(self.template_name, **template_vars)
        # Fallback: serialize context directly
        return json.dumps({
            "premise": context.premise,
            "controlling_design": context.controlling_design,
            "scene_brief": context.scene_brief,
            "style_profile": context.style_profile,
        }, indent=2)

    def build_template_context(self, context: AgentContext) -> dict[str, Any]:
        """Build template variables from agent context. Override in subclasses."""
        return {
            "premise": context.premise,
            "controlling_design": context.controlling_design,
            "style_profile": context.style_profile,
            "chapter_brief": context.chapter_brief,
            "scene_brief": context.scene_brief,
            "characters": context.characters,
            "character_states": context.character_states,
            "preceding_scenes": context.preceding_scenes,
            "open_promises": context.open_promises,
            "extra": context.extra,
        }

    def parse_response(self, response: LLMResponse, context: AgentContext) -> Any:
        """Parse the LLM response. Override for custom parsing logic."""
        # If using tool-based structured output
        if self.response_model and response.tool_use:
            for tool_block in response.tool_use:
                if tool_block["name"] == "respond":
                    try:
                        return self.response_model.model_validate(tool_block["input"])
                    except Exception as e:
                        raise ParseError(self.role, str(e)) from e

        # Try to parse as JSON from text
        if self.response_model and response.text:
            try:
                # Try to extract JSON from the response
                text = response.text.strip()
                if text.startswith("```"):
                    # Strip markdown code blocks
                    lines = text.split("\n")
                    text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
                data = json.loads(text)
                return self.response_model.model_validate(data)
            except (json.JSONDecodeError, Exception) as e:
                raise ParseError(self.role, f"Failed to parse JSON: {e}") from e

        # Return raw text for prose agents
        return response.text

    def _build_tools(self) -> list[dict[str, Any]] | None:
        """Build tool definitions for structured output."""
        if not self.response_model:
            return None
        schema = self.response_model.model_json_schema()
        return [{
            "name": "respond",
            "description": f"Provide your {self.role} response in structured format.",
            "input_schema": schema,
        }]

    # Role-specific labels for the thinking spinner
    _ROLE_LABELS: dict[str, str] = {
        "premise_architect": "Designing the premise",
        "spine_architect": "Building the structural spine",
        "character_designer": "Imagining the cast",
        "style_builder": "Defining the voice",
        "chapter_planner": "Mapping the chapters",
        "scene_planner": "Sketching scenes",
        "scene_writer": None,  # Use rotating verbs for the creative work
        "local_rewriter": "Revising",
        "promise_seeder": "Tracing the promises",
    }

    def _thinking_label(self) -> str | None:
        """Return a spinner label for this agent, or None for rotating verbs."""
        return self._ROLE_LABELS.get(self.role)

    def _max_tokens(self) -> int:
        """Default max tokens. Override for agents that need more."""
        return 4096

    def _temperature(self) -> float:
        """Default temperature. Override for creative vs analytical agents."""
        return 1.0
