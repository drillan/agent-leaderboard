"""Agent execution orchestration.

This module provides single and multi-agent execution functionality
with timeout handling and result collection.
"""

import asyncio
import json
from typing import Any, TypedDict

from pydantic_ai import Agent

from src.agents.eval_agent import format_evaluation_prompt, parse_evaluation_response
from src.config.models import EvaluationConfig, ModelConfig
from src.execution.timeout import with_timeout
from src.models.evaluation import EvaluationResult
from src.models.execution import AgentExecution, ExecutionStatus


class ToolCallNode(TypedDict):
    """Represents a tool call in the hierarchy tree.

    Attributes:
        tool_name: Name of the tool that was called
        args: Arguments passed to the tool
        result: Result returned by the tool (may contain error)
        call_id: Unique identifier for this tool call
        children: List of child tool calls (for nested calls)
    """

    tool_name: str
    args: dict[str, Any]
    result: Any
    call_id: str
    children: list["ToolCallNode"]


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


def extract_agent_response(execution: AgentExecution) -> str:
    """Extract the agent's final response from execution messages.

    Args:
        execution: Completed agent execution with all_messages_json

    Returns:
        The agent's final response text

    Raises:
        ValueError: If messages cannot be parsed or response not found
    """
    if execution.all_messages_json is None:
        raise ValueError("Execution has no messages (possibly timed out)")

    try:
        messages = json.loads(execution.all_messages_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse messages JSON: {e}") from e

    if isinstance(messages, dict) and "error" in messages:
        # Execution failed with an error
        return f"Error: {messages['error']}"

    if not isinstance(messages, list) or len(messages) == 0:
        raise ValueError("No messages found in execution")

    # Find the last assistant/model response message
    # Pydantic AI messages typically have "role" field
    for msg in reversed(messages):
        if isinstance(msg, dict):
            role = msg.get("role", "")
            if role in ("assistant", "model-text-response", "model-structured-response"):
                content = msg.get("content", "")
                if isinstance(content, str) and content.strip():
                    return content.strip()
                # Handle structured content
                if isinstance(content, dict):
                    # Try to extract text from structured content
                    if "text" in content:
                        return str(content["text"]).strip()
                    # Fallback: stringify the entire content
                    return str(content).strip()

    # If no assistant message found, return a description of the execution
    return f"No response found. Status: {execution.status}"


async def evaluate_execution(
    evaluation_agent: Agent,
    eval_config: EvaluationConfig,
    task_prompt: str,
    execution: AgentExecution,
) -> EvaluationResult:
    """Evaluate a completed agent execution.

    Args:
        evaluation_agent: Pydantic AI agent configured for evaluation
        eval_config: Evaluation agent configuration with prompt template
        task_prompt: Original task prompt given to the agent
        execution: Completed agent execution to evaluate

    Returns:
        EvaluationResult with score and explanation

    Raises:
        ValueError: If execution_id is None or execution cannot be evaluated
        ValueError: If evaluation response cannot be parsed
    """
    if execution.id is None:
        raise ValueError("Cannot evaluate execution without database ID")

    # Extract agent's response from messages
    try:
        agent_response = extract_agent_response(execution)
    except ValueError as e:
        # If we can't extract response, create a low-score evaluation
        agent_response = f"Failed to extract response: {e}"

    # Format evaluation prompt
    formatted_prompt = format_evaluation_prompt(
        eval_config.prompt, task_prompt, agent_response
    )

    # Run evaluation agent
    result = await evaluation_agent.run(formatted_prompt)

    # Extract response text from the last message
    # Pydantic AI returns a RunResult, we need to get the text from messages
    messages = result.new_messages()
    response_text = ""

    # Find the last assistant/model message
    for msg in reversed(messages):
        if hasattr(msg, "role") and hasattr(msg, "content"):
            role = str(msg.role)
            if role in ("assistant", "model-text-response"):
                content = msg.content
                if isinstance(content, str):
                    response_text = content
                    break

    if not response_text:
        raise ValueError("No response text found in evaluation agent result")

    # Parse evaluation response
    evaluation = parse_evaluation_response(response_text, execution.id)

    return evaluation


def extract_tool_hierarchy(execution: AgentExecution) -> list[ToolCallNode]:
    """Extract tool call hierarchy from agent execution messages.

    Parses the all_messages_json to build a tree structure of tool calls,
    including nested calls and their results.

    Args:
        execution: Agent execution with all_messages_json

    Returns:
        List of root-level tool call nodes (tools called directly by agent)

    Raises:
        ValueError: If messages cannot be parsed
    """
    if execution.all_messages_json is None:
        return []

    try:
        messages = json.loads(execution.all_messages_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse messages JSON: {e}") from e

    if not isinstance(messages, list):
        # Handle error dict format
        return []

    # Extract tool calls and responses
    tool_calls: dict[str, dict[str, Any]] = {}  # call_id -> tool call info
    tool_responses: dict[str, Any] = {}  # call_id -> result

    for msg in messages:
        if not isinstance(msg, dict):
            continue

        role = msg.get("role", "")

        if role == "tool_call":
            call_id = msg.get("call_id", "")
            if call_id:
                tool_calls[call_id] = {
                    "tool_name": msg.get("tool_name", "unknown"),
                    "args": msg.get("args", {}),
                    "call_id": call_id,
                    "parent_id": msg.get("parent_id"),  # For nested calls
                }

        elif role == "tool_response":
            call_id = msg.get("call_id", "")
            if call_id:
                tool_responses[call_id] = msg.get("content", {})

    # Build hierarchy
    nodes: dict[str, ToolCallNode] = {}
    root_nodes: list[ToolCallNode] = []

    # Create nodes for all tool calls
    for call_id, call_info in tool_calls.items():
        node: ToolCallNode = {
            "tool_name": call_info["tool_name"],
            "args": call_info["args"],
            "result": tool_responses.get(call_id, {}),
            "call_id": call_id,
            "children": [],
        }
        nodes[call_id] = node

        # If no parent, it's a root node
        if not call_info.get("parent_id"):
            root_nodes.append(node)

    # Link children to parents
    for call_id, call_info in tool_calls.items():
        parent_id = call_info.get("parent_id")
        if parent_id and parent_id in nodes:
            parent_node = nodes[parent_id]
            child_node = nodes[call_id]
            parent_node["children"].append(child_node)

    return root_nodes


def calculate_tree_depth(nodes: list[ToolCallNode]) -> int:
    """Calculate the maximum depth of tool call tree.

    Args:
        nodes: List of root-level tool call nodes

    Returns:
        Maximum depth (0 for empty tree, 1 for single level)
    """
    if not nodes:
        return 0

    def get_depth(node: ToolCallNode) -> int:
        if not node["children"]:
            return 1
        return 1 + max(get_depth(child) for child in node["children"])

    return max(get_depth(node) for node in nodes)


def count_leaf_nodes(nodes: list[ToolCallNode]) -> int:
    """Count the number of leaf nodes (nodes with no children).

    Args:
        nodes: List of root-level tool call nodes

    Returns:
        Number of leaf nodes
    """
    if not nodes:
        return 0

    def count_leaves(node: ToolCallNode) -> int:
        if not node["children"]:
            return 1
        return sum(count_leaves(child) for child in node["children"])

    return sum(count_leaves(node) for node in nodes)


def format_tool_call(node: ToolCallNode, max_result_length: int = 100) -> str:
    """Format a tool call node as a human-readable string.

    Args:
        node: Tool call node to format
        max_result_length: Maximum length for result display (truncate if longer)

    Returns:
        Formatted string like "tool_name(arg=value) → result"
    """
    # Format arguments
    args_parts = [f"{k}={v!r}" for k, v in node["args"].items()]
    args_str = ", ".join(args_parts)

    # Format result
    result_str = str(node["result"])
    if len(result_str) > max_result_length:
        result_str = result_str[:max_result_length] + "..."

    return f"{node['tool_name']}({args_str}) → {result_str}"
