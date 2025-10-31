"""Evaluation agent factory for assessing agent task responses.

This module provides functionality to create evaluation agents that assess
the quality of task responses from other agents.
"""

import logging
import re

from pydantic_ai import Agent

from src.config.models import EvaluationConfig

logger = logging.getLogger(__name__)


def create_evaluation_agent(config: EvaluationConfig) -> Agent:
    """Create a Pydantic AI agent for task evaluation.

    Args:
        config: Evaluation agent configuration with provider, model, and prompt

    Returns:
        Configured Pydantic AI Agent for evaluation

    Raises:
        ValueError: If provider is not supported
    """
    from src.config.models import get_pydantic_ai_provider

    # Convert user-friendly provider name to Pydantic AI format
    pydantic_ai_provider = get_pydantic_ai_provider(config.provider)

    # Construct model string based on provider
    model_string = f"{pydantic_ai_provider}{config.model}"

    # Create agent with evaluation system prompt
    agent = Agent(
        model=model_string,
        system_prompt=config.prompt,
    )

    return agent


def parse_evaluation_response(response_text: str) -> tuple[int, str]:
    """Parse evaluation agent response to extract score and explanation.

    Extracts score (0-100) and explanation text from evaluation response.
    Expected format: "Score: [number]" followed by explanation.

    Args:
        response_text: Raw response text from evaluation agent

    Returns:
        Tuple of (score, explanation)

    Raises:
        ValueError: If score cannot be extracted or is invalid
    """
    # Extract score using regex pattern (allows optional negative sign)
    score_match = re.search(r"Score:\s*(-?\d+)", response_text)
    if not score_match:
        raise ValueError("Could not extract score from evaluation response")

    try:
        score = int(score_match.group(1))
    except ValueError as e:
        raise ValueError(
            f"Could not extract score from evaluation response: {e}"
        ) from e

    # Validate score range
    if not 0 <= score <= 100:
        raise ValueError(f"Score must be between 0 and 100, got {score}")

    # Extract explanation after "Explanation:" or remaining text
    explanation_match = re.search(r"Explanation:\s*(.+?)(?:\n|$)", response_text, re.DOTALL)
    if explanation_match:
        explanation = explanation_match.group(1).strip()
    else:
        # Use text after score if no explicit explanation
        score_end = score_match.end()
        remaining = response_text[score_end:].strip()
        explanation = remaining if remaining else "No explanation provided"

    return score, explanation
