"""Unit tests for AI agent implementations.

Tests for task agents and evaluation agents including score extraction and validation.
"""

import json
import os

import pytest

from src.agents.eval_agent import create_evaluation_agent, parse_evaluation_response


class TestEvaluationAgentFactory:
    """Tests for evaluation agent creation."""

    @pytest.fixture(autouse=True)
    def setup_env(self) -> None:
        """Set up mock environment variable for tests."""
        if "GOOGLE_API_KEY" not in os.environ:
            os.environ["GOOGLE_API_KEY"] = "test-api-key"

    def test_create_evaluation_agent(self) -> None:
        """Test creating an evaluation agent with proper configuration."""
        from src.config.models import EvaluationConfig

        eval_config = EvaluationConfig(
            provider="gemini",
            model="gemini-2.5-pro",
            api_key_env="GOOGLE_API_KEY",
            prompt="Evaluate the response.",
        )

        agent = create_evaluation_agent(eval_config)
        assert agent is not None
        # Agent is created successfully with configured prompt

    def test_evaluation_agent_with_custom_prompt(self) -> None:
        """Test evaluation agent respects custom prompt."""
        from src.config.models import EvaluationConfig

        custom_prompt = "Custom evaluation prompt: {task_prompt} {agent_response}"
        eval_config = EvaluationConfig(
            provider="gemini",
            model="gemini-2.5-pro",
            api_key_env="GOOGLE_API_KEY",
            prompt=custom_prompt,
        )

        agent = create_evaluation_agent(eval_config)
        assert agent is not None


class TestEvaluationResponseParsing:
    """Tests for parsing evaluation agent responses."""

    def test_parse_valid_evaluation_response(self) -> None:
        """Test parsing valid evaluation response with score."""
        response_text = """The agent correctly identified that 17 is a prime number.

Score: 95
Explanation: Excellent use of the prime checking tool with clear reasoning."""

        score, explanation = parse_evaluation_response(response_text)

        assert score == 95
        assert explanation == "Excellent use of the prime checking tool with clear reasoning."

    def test_parse_minimum_score(self) -> None:
        """Test parsing evaluation with minimum score (0)."""
        response_text = """Score: 0
Explanation: Completely incorrect response."""

        score, explanation = parse_evaluation_response(response_text)

        assert score == 0
        assert explanation == "Completely incorrect response."

    def test_parse_maximum_score(self) -> None:
        """Test parsing evaluation with maximum score (100)."""
        response_text = """Score: 100
Explanation: Perfect response."""

        score, explanation = parse_evaluation_response(response_text)

        assert score == 100
        assert explanation == "Perfect response."

    def test_parse_score_with_extra_whitespace(self) -> None:
        """Test parsing score with extra whitespace."""
        response_text = """Score:   87
Explanation: Good response with minor issues."""

        score, explanation = parse_evaluation_response(response_text)

        assert score == 87

    def test_parse_invalid_score_raises_error(self) -> None:
        """Test that invalid score raises ValueError."""
        response_text = """Score: invalid
Explanation: Bad response."""

        with pytest.raises(ValueError, match="Could not extract score"):
            parse_evaluation_response(response_text)

    def test_parse_missing_score_raises_error(self) -> None:
        """Test that missing score raises ValueError."""
        response_text = """The response was good.
Explanation: Some explanation."""

        with pytest.raises(ValueError, match="Could not extract score"):
            parse_evaluation_response(response_text)

    def test_parse_score_out_of_range_raises_error(self) -> None:
        """Test that score outside 0-100 raises ValueError."""
        response_text = """Score: 150
Explanation: Invalid score."""

        with pytest.raises(ValueError, match="must be between 0 and 100"):
            parse_evaluation_response(response_text)

    def test_parse_negative_score_raises_error(self) -> None:
        """Test that negative score raises ValueError."""
        response_text = """Score: -5
Explanation: Negative score."""

        with pytest.raises(ValueError, match="must be between 0 and 100"):
            parse_evaluation_response(response_text)


class TestToolHierarchyExtraction:
    """Tests for extracting tool call hierarchy from execution messages."""

    def test_extract_tool_calls_from_messages(self) -> None:
        """Test extracting tool calls from message JSON."""
        from src.execution.executor import extract_tool_calls

        # Mock execution messages with tool calls
        messages_json = json.dumps([
            {
                "kind": "request",
                "parts": [
                    {"type": "text", "content": "Check if 17 is prime"},
                    {"type": "tool_call", "tool_name": "check_prime", "args": {"n": 17}}
                ]
            },
            {
                "kind": "response",
                "parts": [
                    {"type": "text", "content": "17 is prime"},
                    {"type": "tool_result", "tool_name": "check_prime", "result": True}
                ]
            }
        ])

        tool_calls = extract_tool_calls(messages_json)

        assert len(tool_calls) > 0
        # Verify tool calls are properly extracted

    def test_extract_tool_calls_with_no_tools(self) -> None:
        """Test extracting from messages with no tool calls."""
        from src.execution.executor import extract_tool_calls

        messages_json = json.dumps([
            {
                "kind": "request",
                "parts": [{"type": "text", "content": "Simple text query"}]
            }
        ])

        tool_calls = extract_tool_calls(messages_json)

        assert len(tool_calls) == 0

    def test_extract_tool_calls_handles_invalid_json(self) -> None:
        """Test that invalid JSON is handled gracefully."""
        from src.execution.executor import extract_tool_calls

        invalid_json = "not valid json"

        tool_calls = extract_tool_calls(invalid_json)

        # Should handle gracefully and return empty list
        assert isinstance(tool_calls, list)


class TestEvaluationExecutor:
    """Tests for evaluation execution functionality."""

    def test_extract_agent_response_from_messages(self) -> None:
        """Test extracting agent response from messages JSON."""
        from src.execution.evaluator import extract_agent_response

        messages_json = json.dumps([
            {
                "kind": "request",
                "parts": [
                    {"type": "text", "content": "What is 2 + 2?"}
                ]
            },
            {
                "kind": "response",
                "parts": [
                    {"type": "text", "content": "The answer is 4."}
                ]
            }
        ])

        response = extract_agent_response(messages_json)

        assert response == "The answer is 4."
        assert len(response) > 0

    def test_extract_agent_response_with_multiple_parts(self) -> None:
        """Test extracting response when there are multiple text parts."""
        from src.execution.evaluator import extract_agent_response

        messages_json = json.dumps([
            {
                "kind": "response",
                "parts": [
                    {"type": "text", "content": "Let me"},
                    {"type": "text", "content": "calculate:"},
                    {"type": "text", "content": "2 + 2 = 4"}
                ]
            }
        ])

        response = extract_agent_response(messages_json)

        assert "Let me" in response
        assert "calculate:" in response
        assert "4" in response

    def test_extract_agent_response_from_empty_json(self) -> None:
        """Test extracting response from empty messages."""
        from src.execution.evaluator import extract_agent_response

        response = extract_agent_response("")

        assert response == ""

    def test_extract_agent_response_from_none(self) -> None:
        """Test extracting response from None."""
        from src.execution.evaluator import extract_agent_response

        response = extract_agent_response(None)

        assert response == ""

    def test_extract_agent_response_handles_invalid_json(self) -> None:
        """Test that invalid JSON is handled gracefully."""
        from src.execution.evaluator import extract_agent_response

        response = extract_agent_response("not valid json")

        # Should handle gracefully and return empty string
        assert isinstance(response, str)
        assert response == ""

    def test_extract_agent_response_ignores_non_response_messages(self) -> None:
        """Test that only response message kinds are extracted."""
        from src.execution.evaluator import extract_agent_response

        messages_json = json.dumps([
            {
                "kind": "request",
                "parts": [
                    {"type": "text", "content": "This is a request"}
                ]
            },
            {
                "kind": "tool_call",
                "parts": [
                    {"type": "text", "content": "This is a tool call"}
                ]
            },
            {
                "kind": "response",
                "parts": [
                    {"type": "text", "content": "This is the response"}
                ]
            }
        ])

        response = extract_agent_response(messages_json)

        assert response == "This is the response"

    def test_extract_agent_response_with_non_text_parts(self) -> None:
        """Test response extraction with mixed part types."""
        from src.execution.evaluator import extract_agent_response

        messages_json = json.dumps([
            {
                "kind": "response",
                "parts": [
                    {"type": "text", "content": "The result is"},
                    {"type": "tool_result", "content": "ignored"},
                    {"type": "text", "content": "42"}
                ]
            }
        ])

        response = extract_agent_response(messages_json)

        # Should only include text parts
        assert "The result is" in response
        assert "42" in response
