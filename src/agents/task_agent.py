"""Task agent factory for creating Pydantic AI agents.

This module provides functionality to create task execution agents
configured with tools and model settings.
"""

import os

from pydantic_ai import Agent

from src.agents.tools import check_palindrome, check_prime, get_datetime
from src.config.models import ModelConfig


def create_task_agent(config: ModelConfig) -> Agent:
    """Create a Pydantic AI agent for task execution.

    Args:
        config: Model configuration with provider, model name, and API key

    Returns:
        Configured Pydantic AI Agent with all tools registered

    Raises:
        ValueError: If API key environment variable is not set
        ValueError: If provider is not supported
    """
    # Validate API key is available
    api_key = os.getenv(config.api_key_env)
    if not api_key:
        raise ValueError(f"API key environment variable {config.api_key_env} not set")

    # Construct model string based on provider
    model_string = f"{config.provider}:{config.model}"

    # Create agent with tools
    agent = Agent(
        model=model_string,
        tools=[get_datetime, check_prime, check_palindrome],
    )

    return agent


def create_task_agents_from_config(model_configs: list[ModelConfig]) -> list[Agent]:
    """Create multiple task agents from a list of model configurations.

    Args:
        model_configs: List of model configurations

    Returns:
        List of configured Pydantic AI Agents

    Raises:
        ValueError: If any configuration is invalid or API keys are missing
    """
    agents = []
    for config in model_configs:
        agent = create_task_agent(config)
        agents.append(agent)

    return agents
