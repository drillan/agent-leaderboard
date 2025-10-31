"""Agent execution orchestration.

This module provides single and multi-agent execution functionality
with timeout handling and result collection.
"""

import asyncio
import json
from typing import Any

from pydantic_ai import Agent

from src.config.models import ModelConfig
from src.execution.timeout import with_timeout
from src.models.execution import AgentExecution, ExecutionStatus


async def execute_single_agent(
    agent: Agent,
    prompt: str,
    model_config: ModelConfig,
    task_id: int,
    timeout_seconds: float,
) -> AgentExecution:
    """Execute a single agent with timeout handling.

    Args:
        agent: Pydantic AI Agent instance
        prompt: Task prompt to execute
        model_config: Model configuration
        task_id: Database ID of the task
        timeout_seconds: Maximum execution time in seconds

    Returns:
        AgentExecution with results populated (status, duration, all_messages_json)
    """
    # Create execution record
    execution = AgentExecution(
        task_id=task_id,
        model_provider=model_config.provider,
        model_name=model_config.model,
        status=ExecutionStatus.RUNNING,
    )

    try:
        # Execute agent with timeout
        result: Any = await with_timeout(agent.run(prompt), timeout_seconds)

        if result is None:
            # Timeout occurred
            execution.mark_timeout()
            execution.all_messages_json = None
        else:
            # Successful completion
            execution.mark_completed()

            # Extract all messages for tool call tracking
            # Pydantic AI stores messages in result.new_messages()
            new_messages = result.new_messages()
            messages_data = []
            for msg in new_messages:
                # Convert message to dict for JSON serialization
                if hasattr(msg, "model_dump"):
                    messages_data.append(msg.model_dump())
                else:
                    # Fallback for messages without model_dump
                    messages_data.append({"role": str(msg.role), "content": str(msg.content)})

            execution.all_messages_json = json.dumps(messages_data)

            # Extract token count if available
            usage = result.usage()
            if usage is not None:
                execution.token_count = getattr(usage, "total_tokens", None)

    except Exception as e:
        # Execution failed
        execution.mark_failed()
        execution.all_messages_json = json.dumps({"error": str(e)})

    return execution


async def execute_multi_agent(
    agents: list[Agent],
    model_configs: list[ModelConfig],
    prompt: str,
    task_id: int,
    timeout_seconds: float,
) -> list[AgentExecution]:
    """Execute multiple agents in parallel.

    Args:
        agents: List of Pydantic AI Agent instances
        model_configs: List of model configurations (must match agents list)
        prompt: Task prompt to execute
        task_id: Database ID of the task
        timeout_seconds: Maximum execution time in seconds per agent

    Returns:
        List of AgentExecution results (one per agent)

    Raises:
        ValueError: If agents and model_configs lists have different lengths
    """
    if len(agents) != len(model_configs):
        raise ValueError(
            f"Agents count ({len(agents)}) must match model configs count ({len(model_configs)})"
        )

    # Create tasks for parallel execution
    tasks = [
        execute_single_agent(agent, prompt, config, task_id, timeout_seconds)
        for agent, config in zip(agents, model_configs, strict=True)
    ]

    # Execute all agents in parallel
    results = await asyncio.gather(*tasks)

    return list(results)
