"""Agent execution orchestration.

This module provides single and multi-agent execution functionality
with timeout handling and result collection.
"""

import asyncio
import json
import logging
from typing import Any

from pydantic_ai import Agent

from src.config.models import ModelConfig
from src.execution.timeout import with_timeout
from src.models.execution import AgentExecution, ExecutionStatus

logger = logging.getLogger(__name__)


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
            # Use Pydantic AI's built-in JSON serialization
            execution.all_messages_json = result.all_messages_json().decode("utf-8")

            # Extract token count if available
            usage = result.usage()
            if usage is not None:
                execution.token_count = getattr(usage, "total_tokens", None)

    except Exception as e:
        # Execution failed
        execution.mark_failed()
        error_message = str(e)
        execution.all_messages_json = json.dumps({"error": error_message})
        model_id = f"{model_config.provider}/{model_config.model}"
        logger.error(
            f"Agent execution failed for {model_id}: {error_message}",
            exc_info=True,
        )

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


def extract_tool_calls(messages_json: str) -> list[dict[str, Any]]:
    """Extract tool calls from execution messages JSON.

    Parses all_messages_json to extract tool call information
    for building execution hierarchy.

    Args:
        messages_json: JSON string of messages from agent execution

    Returns:
        List of extracted tool calls with metadata

    Example:
        >>> messages_str = '[{"kind":"request","parts":[{"type":"tool_call",'
        >>> messages_str += '"tool_name":"check_prime","args":{"n":17}}]}]'
        >>> calls = extract_tool_calls(messages_str)
        >>> len(calls) > 0
        True
    """
    tool_calls: list[dict[str, Any]] = []

    try:
        messages = json.loads(messages_json)
    except (json.JSONDecodeError, TypeError):
        logger.debug("Could not parse messages JSON for tool call extraction")
        return tool_calls

    if not isinstance(messages, list):
        logger.debug(f"Messages is not a list: {type(messages)}")
        return tool_calls

    logger.debug(f"Extracting tool calls from {len(messages)} messages")

    for message in messages:
        if not isinstance(message, dict):
            continue

        parts = message.get("parts", [])
        if not isinstance(parts, list):
            continue

        for part in parts:
            if not isinstance(part, dict):
                continue

            # Pydantic AI uses "part_kind" instead of "type"
            # Check both for compatibility
            part_kind = part.get("part_kind", "")
            part_type = part.get("type", "")

            if part_kind == "tool-call" or part_type == "tool_call":
                tool_name = part.get("tool_name", "unknown")
                args = part.get("args", {})
                logger.debug(f"Found tool call: {tool_name} with args: {args}")
                tool_call = {
                    "tool_name": tool_name,
                    "args": args,
                    "timestamp": part.get("timestamp") or message.get("timestamp"),
                }
                tool_calls.append(tool_call)

    logger.debug(f"Extracted {len(tool_calls)} tool calls total")
    return tool_calls
