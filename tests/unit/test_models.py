"""Unit tests for domain models.

Tests for task submissions, agent executions, evaluations, and performance metrics.
"""

from datetime import datetime, timedelta

import pytest

from src.models.evaluation import EvaluationResult
from src.models.execution import AgentExecution, ExecutionStatus
from src.models.metrics import PerformanceMetrics
from src.models.task import TaskSubmission


class TestTaskSubmission:
    """Tests for TaskSubmission domain model."""

    def test_valid_task_with_id(self) -> None:
        """Test creating a valid task with ID."""
        task = TaskSubmission(id=1, prompt="Calculate the factorial of 5")
        assert task.id == 1
        assert task.prompt == "Calculate the factorial of 5"
        assert isinstance(task.submitted_at, datetime)

    def test_valid_task_without_id(self) -> None:
        """Test creating a new task without ID."""
        task = TaskSubmission(prompt="What is the weather today?")
        assert task.id is None
        assert task.prompt == "What is the weather today?"

    def test_empty_prompt_rejected(self) -> None:
        """Test that empty prompt is rejected."""
        with pytest.raises(ValueError):
            TaskSubmission(prompt="")

    def test_whitespace_only_prompt_rejected(self) -> None:
        """Test that whitespace-only prompt is rejected."""
        with pytest.raises(ValueError, match="must not be empty"):
            TaskSubmission(prompt="   \n\t   ")

    def test_prompt_trimmed_property(self) -> None:
        """Test prompt_trimmed property removes whitespace."""
        task = TaskSubmission(prompt="  Hello World  \n")
        assert task.prompt_trimmed == "Hello World"

    def test_submitted_at_is_recent(self) -> None:
        """Test that submitted_at is set to current time."""
        before = datetime.now()
        task = TaskSubmission(prompt="Test task")
        after = datetime.now()
        assert before <= task.submitted_at <= after


class TestExecutionStatus:
    """Tests for ExecutionStatus enum."""

    def test_all_status_values(self) -> None:
        """Test all execution status values."""
        assert ExecutionStatus.RUNNING.value == "running"
        assert ExecutionStatus.COMPLETED.value == "completed"
        assert ExecutionStatus.FAILED.value == "failed"
        assert ExecutionStatus.TIMEOUT.value == "timeout"

    def test_status_string_conversion(self) -> None:
        """Test status can be compared with strings."""
        status = ExecutionStatus.RUNNING
        assert status == "running"
        assert status.value == "running"


class TestAgentExecution:
    """Tests for AgentExecution domain model."""

    def test_valid_execution(self) -> None:
        """Test creating a valid agent execution."""
        execution = AgentExecution(
            task_id=1,
            model_provider="openai",
            model_name="gpt-4o",
            token_count=150,
        )
        assert execution.task_id == 1
        assert execution.model_provider == "openai"
        assert execution.model_name == "gpt-4o"
        assert execution.status == ExecutionStatus.RUNNING
        assert execution.token_count == 150

    def test_default_status_is_running(self) -> None:
        """Test that status defaults to RUNNING."""
        execution = AgentExecution(
            task_id=1, model_provider="anthropic", model_name="claude-sonnet-4"
        )
        assert execution.status == ExecutionStatus.RUNNING
        assert execution.completed_at is None

    def test_started_at_is_recent(self) -> None:
        """Test that started_at is set to current time."""
        before = datetime.now()
        execution = AgentExecution(
            task_id=1, model_provider="openai", model_name="gpt-4o"
        )
        after = datetime.now()
        assert before <= execution.started_at <= after

    def test_calculate_duration(self) -> None:
        """Test duration calculation from timestamps."""
        execution = AgentExecution(
            task_id=1, model_provider="openai", model_name="gpt-4o"
        )
        execution.started_at = datetime(2025, 1, 1, 12, 0, 0)
        execution.completed_at = datetime(2025, 1, 1, 12, 0, 30)
        execution.calculate_duration()
        assert execution.duration_seconds == 30.0

    def test_calculate_duration_with_fractional_seconds(self) -> None:
        """Test duration calculation with fractional seconds."""
        execution = AgentExecution(
            task_id=1, model_provider="openai", model_name="gpt-4o"
        )
        execution.started_at = datetime.now()
        execution.completed_at = execution.started_at + timedelta(seconds=45.5)
        execution.calculate_duration()
        assert execution.duration_seconds == 45.5

    def test_calculate_duration_without_completion(self) -> None:
        """Test that duration is not calculated if not completed."""
        execution = AgentExecution(
            task_id=1, model_provider="openai", model_name="gpt-4o"
        )
        execution.calculate_duration()
        assert execution.duration_seconds is None

    def test_mark_completed(self) -> None:
        """Test marking execution as completed."""
        execution = AgentExecution(
            task_id=1, model_provider="openai", model_name="gpt-4o"
        )
        execution.mark_completed()
        assert execution.status == ExecutionStatus.COMPLETED
        assert execution.completed_at is not None
        assert execution.duration_seconds is not None
        assert execution.duration_seconds > 0

    def test_mark_failed(self) -> None:
        """Test marking execution as failed."""
        execution = AgentExecution(
            task_id=1, model_provider="openai", model_name="gpt-4o"
        )
        execution.mark_failed()
        assert execution.status == ExecutionStatus.FAILED
        assert execution.completed_at is not None
        assert execution.duration_seconds is not None

    def test_mark_timeout(self) -> None:
        """Test marking execution as timed out."""
        execution = AgentExecution(
            task_id=1, model_provider="openai", model_name="gpt-4o"
        )
        execution.mark_timeout()
        assert execution.status == ExecutionStatus.TIMEOUT
        assert execution.completed_at is not None
        assert execution.duration_seconds is not None

    def test_negative_token_count_rejected(self) -> None:
        """Test that negative token count is rejected."""
        with pytest.raises(ValueError):
            AgentExecution(
                task_id=1,
                model_provider="openai",
                model_name="gpt-4o",
                token_count=-10,
            )

    def test_zero_token_count_accepted(self) -> None:
        """Test that zero token count is accepted."""
        execution = AgentExecution(
            task_id=1, model_provider="openai", model_name="gpt-4o", token_count=0
        )
        assert execution.token_count == 0


class TestEvaluationResult:
    """Tests for EvaluationResult domain model."""

    def test_valid_evaluation(self) -> None:
        """Test creating a valid evaluation."""
        evaluation = EvaluationResult(
            execution_id=1, score=85, explanation="Good performance on the task"
        )
        assert evaluation.execution_id == 1
        assert evaluation.score == 85
        assert evaluation.explanation == "Good performance on the task"
        assert isinstance(evaluation.evaluated_at, datetime)

    def test_score_minimum_boundary(self) -> None:
        """Test score minimum boundary (0)."""
        evaluation = EvaluationResult(
            execution_id=1, score=0, explanation="Failed completely"
        )
        assert evaluation.score == 0

    def test_score_maximum_boundary(self) -> None:
        """Test score maximum boundary (100)."""
        evaluation = EvaluationResult(
            execution_id=1, score=100, explanation="Perfect execution"
        )
        assert evaluation.score == 100

    def test_score_below_minimum_rejected(self) -> None:
        """Test that score below 0 is rejected."""
        with pytest.raises(ValueError):
            EvaluationResult(execution_id=1, score=-1, explanation="Test")

    def test_score_above_maximum_rejected(self) -> None:
        """Test that score above 100 is rejected."""
        with pytest.raises(ValueError):
            EvaluationResult(execution_id=1, score=101, explanation="Test")

    def test_empty_explanation_rejected(self) -> None:
        """Test that empty explanation is rejected."""
        with pytest.raises(ValueError):
            EvaluationResult(execution_id=1, score=50, explanation="")

    def test_whitespace_only_explanation_rejected(self) -> None:
        """Test that whitespace-only explanation is rejected."""
        with pytest.raises(ValueError, match="must not be empty"):
            EvaluationResult(execution_id=1, score=50, explanation="   \n\t   ")

    def test_explanation_trimmed_property(self) -> None:
        """Test explanation_trimmed property removes whitespace."""
        evaluation = EvaluationResult(
            execution_id=1, score=75, explanation="  Good work  \n"
        )
        assert evaluation.explanation_trimmed == "Good work"

    def test_is_passing_below_threshold(self) -> None:
        """Test is_passing returns False for score below 50."""
        evaluation = EvaluationResult(execution_id=1, score=49, explanation="Test")
        assert evaluation.is_passing is False

    def test_is_passing_at_threshold(self) -> None:
        """Test is_passing returns True for score at 50."""
        evaluation = EvaluationResult(execution_id=1, score=50, explanation="Test")
        assert evaluation.is_passing is True

    def test_is_passing_above_threshold(self) -> None:
        """Test is_passing returns True for score above 50."""
        evaluation = EvaluationResult(execution_id=1, score=51, explanation="Test")
        assert evaluation.is_passing is True

    def test_grade_a(self) -> None:
        """Test grade A (90-100)."""
        evaluation = EvaluationResult(execution_id=1, score=95, explanation="Test")
        assert evaluation.grade == "A"

    def test_grade_b(self) -> None:
        """Test grade B (80-89)."""
        evaluation = EvaluationResult(execution_id=1, score=85, explanation="Test")
        assert evaluation.grade == "B"

    def test_grade_c(self) -> None:
        """Test grade C (70-79)."""
        evaluation = EvaluationResult(execution_id=1, score=75, explanation="Test")
        assert evaluation.grade == "C"

    def test_grade_d(self) -> None:
        """Test grade D (60-69)."""
        evaluation = EvaluationResult(execution_id=1, score=65, explanation="Test")
        assert evaluation.grade == "D"

    def test_grade_f(self) -> None:
        """Test grade F (0-59)."""
        evaluation = EvaluationResult(execution_id=1, score=45, explanation="Test")
        assert evaluation.grade == "F"

    def test_grade_boundary_90(self) -> None:
        """Test grade boundary at 90."""
        eval_89 = EvaluationResult(execution_id=1, score=89, explanation="Test")
        eval_90 = EvaluationResult(execution_id=1, score=90, explanation="Test")
        assert eval_89.grade == "B"
        assert eval_90.grade == "A"

    def test_evaluated_at_is_recent(self) -> None:
        """Test that evaluated_at is set to current time."""
        before = datetime.now()
        evaluation = EvaluationResult(execution_id=1, score=75, explanation="Test")
        after = datetime.now()
        assert before <= evaluation.evaluated_at <= after


class TestPerformanceMetrics:
    """Tests for PerformanceMetrics domain model."""

    def test_valid_metrics(self) -> None:
        """Test creating valid performance metrics."""
        metrics = PerformanceMetrics(
            execution_id=1,
            duration_seconds=30.5,
            token_count=1500,
            model_provider="openai",
            model_name="gpt-4o",
        )
        assert metrics.execution_id == 1
        assert metrics.duration_seconds == 30.5
        assert metrics.token_count == 1500
        assert metrics.model_provider == "openai"
        assert metrics.model_name == "gpt-4o"

    def test_duration_ms_property(self) -> None:
        """Test duration_ms property converts seconds to milliseconds."""
        metrics = PerformanceMetrics(
            execution_id=1,
            duration_seconds=2.5,
            token_count=100,
            model_provider="openai",
            model_name="gpt-4o",
        )
        assert metrics.duration_ms == 2500.0

    def test_tokens_per_second_property(self) -> None:
        """Test tokens_per_second calculation."""
        metrics = PerformanceMetrics(
            execution_id=1,
            duration_seconds=10.0,
            token_count=500,
            model_provider="openai",
            model_name="gpt-4o",
        )
        assert metrics.tokens_per_second == 50.0

    def test_tokens_per_second_with_fractional_duration(self) -> None:
        """Test tokens_per_second with fractional duration."""
        metrics = PerformanceMetrics(
            execution_id=1,
            duration_seconds=2.5,
            token_count=100,
            model_provider="openai",
            model_name="gpt-4o",
        )
        assert metrics.tokens_per_second == 40.0

    def test_tokens_per_second_with_zero_tokens(self) -> None:
        """Test tokens_per_second with zero tokens."""
        metrics = PerformanceMetrics(
            execution_id=1,
            duration_seconds=5.0,
            token_count=0,
            model_provider="openai",
            model_name="gpt-4o",
        )
        assert metrics.tokens_per_second == 0.0

    def test_model_identifier_property(self) -> None:
        """Test model_identifier property combines provider and name."""
        metrics = PerformanceMetrics(
            execution_id=1,
            duration_seconds=5.0,
            token_count=100,
            model_provider="anthropic",
            model_name="claude-sonnet-4",
        )
        assert metrics.model_identifier == "anthropic/claude-sonnet-4"

    def test_zero_duration_rejected(self) -> None:
        """Test that zero duration is rejected."""
        with pytest.raises(ValueError):
            PerformanceMetrics(
                execution_id=1,
                duration_seconds=0.0,
                token_count=100,
                model_provider="openai",
                model_name="gpt-4o",
            )

    def test_negative_duration_rejected(self) -> None:
        """Test that negative duration is rejected."""
        with pytest.raises(ValueError):
            PerformanceMetrics(
                execution_id=1,
                duration_seconds=-5.0,
                token_count=100,
                model_provider="openai",
                model_name="gpt-4o",
            )

    def test_negative_token_count_rejected(self) -> None:
        """Test that negative token count is rejected."""
        with pytest.raises(ValueError):
            PerformanceMetrics(
                execution_id=1,
                duration_seconds=5.0,
                token_count=-100,
                model_provider="openai",
                model_name="gpt-4o",
            )
