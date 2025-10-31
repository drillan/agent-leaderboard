"""Evaluation agent factory for creating Pydantic AI evaluation agents.

This module provides functionality to create evaluation agents
that assess task execution quality and generate scores with explanations.
"""

import os
import re
from datetime import datetime

from pydantic_ai import Agent

from src.config.models import EvaluationConfig
from src.models.evaluation import EvaluationResult


def create_evaluation_agent(config: EvaluationConfig) -> Agent:
    """Create a Pydantic AI agent for evaluating task executions.

    Args:
        config: Evaluation configuration with provider, model, API key, and prompt

    Returns:
        Configured Pydantic AI Agent for evaluation

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

    # Create agent without tools (evaluation agent doesn't need tools)
    agent = Agent(
        model=model_string,
    )

    return agent


def format_evaluation_prompt(
    prompt_template: str, task_prompt: str, agent_response: str
) -> str:
    """Format evaluation prompt by substituting placeholders.

    Args:
        prompt_template: Template string with {task_prompt} and {agent_response}
        task_prompt: The original task given to the agent
        agent_response: The agent's response to evaluate

    Returns:
        Formatted prompt with substituted values

    Raises:
        ValueError: If required placeholders are missing
    """
    if "{task_prompt}" not in prompt_template:
        raise ValueError("Prompt template missing {task_prompt} placeholder")
    if "{agent_response}" not in prompt_template:
        raise ValueError("Prompt template missing {agent_response} placeholder")

    return prompt_template.format(
        task_prompt=task_prompt, agent_response=agent_response
    )


def extract_score(text: str) -> int:
    """Extract numeric score from evaluation response text.

    Args:
        text: Response text containing score

    Returns:
        Extracted score (0-100)

    Raises:
        ValueError: If score cannot be extracted or is out of range
    """
    # Try to find "Score: <number>" pattern
    score_match = re.search(r"Score:\s*(\d+)", text, re.IGNORECASE)
    if score_match:
        score = int(score_match.group(1))
        if 0 <= score <= 100:
            return score
        raise ValueError(f"Score {score} is out of range (0-100)")

    # Try to find any standalone number between 0-100
    numbers = re.findall(r"\b(\d+)\b", text)
    for num_str in numbers:
        num = int(num_str)
        if 0 <= num <= 100:
            return num

    raise ValueError(f"Could not extract valid score from text: {text[:100]}")


def extract_explanation(text: str) -> str:
    """Extract explanation text from evaluation response.

    Args:
        text: Response text containing explanation

    Returns:
        Extracted explanation text

    Raises:
        ValueError: If explanation cannot be extracted or is empty
    """
    # Try to find "Explanation: <text>" pattern
    explanation_match = re.search(
        r"Explanation:\s*(.+)", text, re.IGNORECASE | re.DOTALL
    )
    if explanation_match:
        explanation = explanation_match.group(1).strip()
        if explanation:
            return explanation

    # If no "Explanation:" prefix found, try to extract text after score
    score_pattern = re.search(r"Score:\s*\d+\s*(.+)", text, re.IGNORECASE | re.DOTALL)
    if score_pattern:
        explanation = score_pattern.group(1).strip()
        if explanation:
            return explanation

    # Last resort: use entire text if it's non-empty
    cleaned_text = text.strip()
    if cleaned_text:
        return cleaned_text

    raise ValueError("Could not extract explanation from response")


def parse_evaluation_response(response_text: str, execution_id: int) -> EvaluationResult:
    """Parse evaluation agent response into EvaluationResult.

    Args:
        response_text: Raw response text from evaluation agent
        execution_id: ID of the execution being evaluated

    Returns:
        Parsed EvaluationResult with score and explanation

    Raises:
        ValueError: If response cannot be parsed or is invalid
    """
    try:
        score = extract_score(response_text)
    except ValueError as e:
        raise ValueError(f"Failed to extract score: {e}") from e

    try:
        explanation = extract_explanation(response_text)
    except ValueError as e:
        raise ValueError(f"Failed to extract explanation: {e}") from e

    return EvaluationResult(
        execution_id=execution_id,
        score=score,
        explanation=explanation,
        evaluated_at=datetime.now(),
    )
