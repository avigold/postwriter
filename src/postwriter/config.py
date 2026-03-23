"""Application configuration via environment variables and .env files."""

from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    model_config = {"env_prefix": "PW_DB_"}

    url: str = "postgresql+asyncpg://postwriter:postwriter@localhost:5450/postwriter"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10


class RedisSettings(BaseSettings):
    model_config = {"env_prefix": "PW_REDIS_"}

    url: str = "redis://localhost:6379/0"


class LLMSettings(BaseSettings):
    model_config = {"env_prefix": "PW_LLM_"}

    anthropic_api_key: str = ""
    opus_model: str = "claude-opus-4-6"
    sonnet_model: str = "claude-sonnet-4-6"
    haiku_model: str = "claude-haiku-4-5-20251001"

    # Rate limiting
    max_concurrent_opus: int = 2
    max_concurrent_sonnet: int = 5
    max_concurrent_haiku: int = 10

    # Token budgets (0 = unlimited)
    opus_token_budget: int = 0
    sonnet_token_budget: int = 0
    haiku_token_budget: int = 0


class OrchestratorSettings(BaseSettings):
    model_config = {"env_prefix": "PW_ORCH_"}

    max_repair_rounds: int = 3
    min_improvement_delta: float = 0.02
    default_branch_count: int = 3
    pivotal_branch_count: int = 5
    canon_slice_max_tokens: int = 80_000
    rolling_window_scenes: int = 3


class Settings(BaseSettings):
    """Top-level settings aggregating all subsystems."""

    model_config = {"env_prefix": "PW_", "env_file": ".env", "env_file_encoding": "utf-8"}

    project_name: str = "postwriter"
    debug: bool = False

    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    orchestrator: OrchestratorSettings = Field(default_factory=OrchestratorSettings)


def get_settings() -> Settings:
    return Settings()
