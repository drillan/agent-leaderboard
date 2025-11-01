"""Configuration data models for the agent leaderboard system.

This module defines Pydantic models for validating and managing
application configuration loaded from TOML files.
"""

import os
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ModelConfig(BaseModel):
    """Configuration for a single AI model (task agent or evaluation agent).

    Attributes:
        provider: AI provider name (openai, anthropic, gemini, groq, or huggingface)
        model: Model identifier (e.g., "gpt-4o", "claude-sonnet-4")
        api_key_env: Environment variable name containing the API key
    """

    provider: Literal["openai", "anthropic", "gemini", "groq", "huggingface"]
    model: str = Field(min_length=1)
    api_key_env: str = Field(min_length=1)

    @field_validator("api_key_env")
    @classmethod
    def validate_api_key_env(cls, v: str) -> str:
        """Validate that the API key environment variable exists.

        Args:
            v: Environment variable name

        Returns:
            The validated environment variable name

        Raises:
            ValueError: If the environment variable is not set
        """
        if v not in os.environ:
            raise ValueError(f"Environment variable {v} not found")
        if not os.environ[v].strip():
            raise ValueError(f"Environment variable {v} is empty")
        return v


class ExecutionConfig(BaseModel):
    """Configuration for task execution behavior.

    Attributes:
        timeout_seconds: Maximum execution time per agent (1-600 seconds)
    """

    timeout_seconds: int = Field(default=60, ge=1, le=600)


class EvaluationConfig(BaseModel):
    """Configuration for the evaluation agent.

    Attributes:
        provider: AI provider name (openai, anthropic, gemini, groq, or huggingface)
        model: Model identifier
        api_key_env: Environment variable name containing the API key
        prompt: Evaluation prompt template with {task_prompt} and {agent_response} placeholders
    """

    provider: Literal["openai", "anthropic", "gemini", "groq", "huggingface"]
    model: str = Field(min_length=1)
    api_key_env: str = Field(min_length=1)
    prompt: str = Field(min_length=1)

    @field_validator("api_key_env")
    @classmethod
    def validate_api_key_env(cls, v: str) -> str:
        """Validate that the API key environment variable exists.

        Args:
            v: Environment variable name

        Returns:
            The validated environment variable name

        Raises:
            ValueError: If the environment variable is not set
        """
        if v not in os.environ:
            raise ValueError(f"Environment variable {v} not found")
        if not os.environ[v].strip():
            raise ValueError(f"Environment variable {v} is empty")
        return v


class DatabaseConfig(BaseModel):
    """Configuration for DuckDB database.

    Attributes:
        path: Path to the DuckDB database file
    """

    path: str = Field(default="agent_leaderboard.duckdb")


class AppConfig(BaseModel):
    """Application configuration root model.

    Attributes:
        execution: Execution behavior configuration
        task_agents: List of task agent configurations (2-5 agents)
        evaluation_agent: Evaluation agent configuration
        database: Database configuration
    """

    execution: ExecutionConfig
    task_agents: list[ModelConfig] = Field(min_length=2, max_length=5)
    evaluation_agent: EvaluationConfig
    database: DatabaseConfig

    @field_validator("task_agents")
    @classmethod
    def validate_unique_models(cls, v: list[ModelConfig]) -> list[ModelConfig]:
        """Validate that all task agent models are unique.

        Args:
            v: List of model configurations

        Returns:
            The validated list of model configurations

        Raises:
            ValueError: If duplicate models are detected
        """
        models = [(m.provider, m.model) for m in v]
        if len(models) != len(set(models)):
            raise ValueError("Duplicate models detected in task_agents")
        return v


def get_pydantic_ai_provider(provider: str) -> str:
    """Convert user-friendly provider name to Pydantic AI format.

    Maps simplified provider names used in configuration to the complete
    provider strings required by Pydantic AI for model inference.

    Args:
        provider: User-friendly provider name (openai, anthropic, gemini, groq, or huggingface)

    Returns:
        Pydantic AI provider string (e.g., 'openai', 'anthropic', 'google-gla:', 'groq:',
        'huggingface:')

    Raises:
        ValueError: If provider is not recognized

    Example:
        >>> get_pydantic_ai_provider("gemini")
        'google-gla:'
        >>> get_pydantic_ai_provider("openai")
        'openai'
        >>> get_pydantic_ai_provider("groq")
        'groq:'
        >>> get_pydantic_ai_provider("huggingface")
        'huggingface:'
    """
    mapping: dict[str, str] = {
        "openai": "openai",
        "anthropic": "anthropic",
        "gemini": "google-gla:",  # Google AI Studio (Generative Language API)
        "groq": "groq:",  # Groq API
        "huggingface": "huggingface:",  # Hugging Face Inference Providers
    }
    if provider not in mapping:
        raise ValueError(
            f"Unknown provider: {provider}. Must be one of: {', '.join(mapping.keys())}"
        )
    return mapping[provider]
