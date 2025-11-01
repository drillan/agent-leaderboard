"""Evaluation execution orchestration.

This module provides functionality to evaluate agent task responses
using an evaluation agent and extract scores and explanations.
"""

import json
import logging
from typing import Any

from pydantic_ai import Agent

from src.execution.timeout import with_timeout
from src.models.evaluation import EvaluationResult
from src.models.execution import AgentExecution

logger = logging.getLogger(__name__)


async def evaluate_execution(
    execution: AgentExecution,
    task_prompt: str,
    agent_response: str,
    eval_agent: Agent,
    timeout_seconds: float = 30.0,
) -> EvaluationResult:
    """Evaluate an agent execution using the evaluation agent.

    Args:
        execution: The AgentExecution instance to evaluate
        task_prompt: Original task prompt given to the agent
        agent_response: Response from the agent (extracted from execution)
        eval_agent: Pydantic AI evaluation agent instance
        timeout_seconds: Maximum execution time for evaluation (default: 30s)

    Returns:
        EvaluationResult with score (0-100) and explanation

    Raises:
        ValueError: If score extraction fails or score is invalid
        TimeoutError: If evaluation exceeds timeout_seconds
        Exception: If evaluation agent execution fails
    """
    print("\n=== STARTING EVALUATION ===")
    print(f"Execution ID: {execution.id}")
    print(f"Task prompt: {task_prompt[:100]}")
    print(f"Agent response length: {len(agent_response)}")
    print(f"Agent response: {agent_response[:200]}")

    # Create evaluation prompt combining task and agent response
    evaluation_prompt = f"""
Task Prompt:
{task_prompt}

Agent Response:
{agent_response}

Please evaluate the agent's response on a scale of 0-100 and provide an explanation.
Format your response as:
Score: [number]
Explanation: [your explanation]
"""

    try:
        # Run evaluation agent with timeout
        result: Any = await with_timeout(eval_agent.run(evaluation_prompt), timeout_seconds)

        if result is None:
            raise TimeoutError(f"Evaluation timed out after {timeout_seconds} seconds")

        # Extract response text from Pydantic AI result
        response_text = ""

        print("\n=== EVALUATION RESULT DEBUG ===")
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")

        # Method 1: Try to access output attribute directly (Pydantic AI result.output)
        try:
            if hasattr(result, "output"):
                response_text = str(result.output)
                print(f"✓ Extracted text using result.output: {response_text[:100]}")
                logger.debug(f"Extracted text using result.output: {response_text[:100]}")
            else:
                print("✗ No 'output' attribute")
        except Exception as e:
            print(f"✗ Error extracting from result.output: {e}")
            logger.debug(f"Could not extract from result.output: {e}")

        if not response_text:
            logger.error(f"Failed to extract response text. Result object: {result}")
            raise ValueError("No response text found in evaluation agent result")

        # Parse score and explanation directly from response text
        # Use the parsing functions from eval_agent module
        from src.agents.eval_agent import extract_explanation, extract_score

        try:
            score = extract_score(response_text)
            print(f"✓ Extracted score: {score}")
            logger.debug(f"Extracted score: {score}")
        except Exception as e:
            print(f"✗ Error extracting score: {e}")
            logger.error(f"Failed to extract score: {e}")
            raise

        try:
            explanation = extract_explanation(response_text)
            print(f"✓ Extracted explanation: {explanation[:100]}")
            logger.debug(f"Extracted explanation: {explanation[:100]}")
        except Exception as e:
            print(f"✗ Error extracting explanation: {e}")
            logger.error(f"Failed to extract explanation: {e}")
            raise

        # Create evaluation result
        evaluation = EvaluationResult(
            execution_id=execution.id or 0,  # execution.id should be set before calling
            score=score,
            explanation=explanation,
        )

        logger.info(
            f"Evaluated execution {execution.id}: score={score}, "
            f"explanation_length={len(explanation)}"
        )

        return evaluation

    except TimeoutError as e:
        logger.error(f"Evaluation timed out for execution {execution.id}: {e}")
        raise
    except ValueError as e:
        logger.error(f"Failed to parse evaluation response for execution {execution.id}: {e}")
        raise
    except Exception as e:
        logger.error(
            f"Evaluation execution failed for execution {execution.id}: {str(e)}",
            exc_info=True,
        )
        raise


def extract_agent_response(messages_json: str | None) -> str:
    """Extract agent response text from execution messages JSON.

    Parses all_messages_json to extract the agent's final response text.

    Args:
        messages_json: JSON string of messages from agent execution

    Returns:
        Agent response text, or empty string if not found

    Example:
        >>> messages = (
        ...     '[{"kind":"response","parts":['
        ...     '{"type":"text","content":"The answer is..."}]}]'
        ... )
        >>> response = extract_agent_response(messages)
        >>> len(response) > 0
        True
    """
    if not messages_json:
        logger.debug("No messages JSON provided")
        return ""

    # Log first 1000 chars of messages JSON for debugging
    logger.debug(f"Messages JSON (first 1000 chars): {messages_json[:1000]}")

    try:
        messages = json.loads(messages_json)
    except (json.JSONDecodeError, TypeError) as e:
        logger.debug(f"Could not parse messages JSON: {e}")
        return ""

    logger.debug(f"Parsed messages type: {type(messages)}, is_list: {isinstance(messages, list)}")

    if not isinstance(messages, list):
        logger.debug(f"Messages is not a list, it's {type(messages)}")
        # Try to extract from dict if it's not a list
        if isinstance(messages, dict):
            logger.debug(f"Messages is dict with keys: {list(messages.keys())}")
        return ""

    logger.debug(f"Total messages: {len(messages)}")
    response_parts = []

    # Iterate through messages to find response content
    # Pydantic AI uses different structure than expected:
    # - Uses "part_kind" (tool-call, tool-return, user-prompt) instead of "type"
    # - Text may be in "content" field or we may need to reconstruct from context
    for i, message in enumerate(messages):
        if not isinstance(message, dict):
            logger.debug(f"Message {i} is not dict: {type(message)}")
            continue

        logger.debug(f"Message {i} keys: {list(message.keys())}")

        # Look for response messages
        if message.get("kind") == "response":
            parts = message.get("parts", [])
            logger.debug(f"Found response message with {len(parts)} parts")
            if isinstance(parts, list):
                for part in parts:
                    if not isinstance(part, dict):
                        continue

                    part_kind = part.get("part_kind", "")
                    logger.debug(f"  Part kind: {part_kind}")

                    # Pydantic AI message structures:
                    # 1. Direct text responses have content field
                    # 2. Tool calls/returns have part_kind but may have content
                    # Extract any content field as potential response text
                    content = part.get("content", "")
                    if content and part_kind != "tool-call" and part_kind != "tool-return":
                        # Skip tool-related parts, look for actual text responses
                        response_parts.append(content)
                        logger.debug(f"Extracted content: {str(content)[:100]}")

            # For tool-using agents, the final response may be implicit
            # (tool was called and result was returned)
            # If no text response found but tool was called, that might be the response

    result = " ".join(response_parts).strip()
    logger.debug(f"Final extracted response length: {len(result)}")

    # If we found no text response but there were tool calls, construct a message
    # from the tool names and results
    if not result and isinstance(messages, list) and len(messages) > 0:
        logger.debug("No text response found, checking for tool-based response")
        tool_info = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            parts = message.get("parts", [])
            if isinstance(parts, list):
                for part in parts:
                    if isinstance(part, dict):
                        # Collect tool calls
                        if part.get("part_kind") == "tool-call":
                            tool_name = part.get("tool_name", "unknown tool")
                            tool_info.append(f"Called {tool_name}")
                            logger.debug(f"Found tool call: {tool_name}")
                        # Collect tool results
                        elif part.get("part_kind") == "tool-return":
                            tool_content = part.get("content", "")
                            if tool_content:
                                tool_info.append(f"Result: {tool_content}")
                                logger.debug(f"Found tool result: {tool_content[:100]}")

        if tool_info:
            result = " ".join(tool_info).strip()
            logger.debug(f"Reconstructed response from tools: {result[:100]}")

    return result
