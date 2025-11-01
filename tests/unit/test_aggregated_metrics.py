"""Unit tests for aggregated performance metrics.

Tests for the updated get_performance_metrics function that returns
aggregated statistics (average, std dev, count) per model.
"""

import pytest

from src.database.connection import DatabaseConnection
from src.database.repositories import TaskRepository
from src.models.execution import AgentExecution
from src.models.task import TaskSubmission


@pytest.fixture
def temp_db() -> DatabaseConnection:
    """Create a temporary in-memory database for testing with schema."""
    db = DatabaseConnection(":memory:")
    db.initialize_schema()
    return db


class TestAggregatedPerformanceMetrics:
    """Tests for aggregated performance metrics query."""

    def test_single_execution_per_model(self, temp_db: DatabaseConnection) -> None:
        """Test metrics with single execution per model (std dev should be 0)."""
        repo = TaskRepository(temp_db)

        # Create task
        task = TaskSubmission(prompt="Test task")
        task_id = repo.create_task(task)

        # Create executions for two different models
        exec1 = AgentExecution(
            task_id=task_id, model_provider="groq", model_name="llama-3.3-70b-versatile"
        )
        exec1.mark_completed()
        exec1.duration_seconds = 1.5
        exec1.token_count = 100
        repo.create_execution(exec1)

        exec2 = AgentExecution(task_id=task_id, model_provider="groq", model_name="qwen3-32b")
        exec2.mark_completed()
        exec2.duration_seconds = 2.0
        exec2.token_count = 150
        repo.create_execution(exec2)

        # Query metrics
        metrics = repo.get_performance_metrics(task_id)

        # Verify
        assert len(metrics) == 2

        # First model
        assert metrics[0]["model_provider"] == "groq"
        assert metrics[0]["model_name"] == "llama-3.3-70b-versatile"
        assert metrics[0]["avg_duration"] == 1.5
        assert metrics[0]["std_duration"] == 0.0  # Single execution
        assert metrics[0]["min_duration"] == 1.5
        assert metrics[0]["max_duration"] == 1.5
        assert metrics[0]["avg_tokens"] == 100.0
        assert metrics[0]["execution_count"] == 1

    def test_multiple_executions_same_model(self, temp_db: DatabaseConnection) -> None:
        """Test metrics with multiple executions of same model."""
        repo = TaskRepository(temp_db)

        # Create task
        task = TaskSubmission(prompt="Test task")
        task_id = repo.create_task(task)

        # Create 3 executions of same model with different durations
        durations = [1.0, 2.0, 3.0]  # avg=2.0, std≈1.0
        tokens = [100, 200, 150]  # avg=150, std≈50

        for dur, tok in zip(durations, tokens, strict=True):
            execution = AgentExecution(
                task_id=task_id, model_provider="groq", model_name="llama-3.3-70b-versatile"
            )
            execution.mark_completed()
            execution.duration_seconds = dur
            execution.token_count = tok
            repo.create_execution(execution)

        # Query metrics
        metrics = repo.get_performance_metrics(task_id)

        # Verify
        assert len(metrics) == 1
        assert metrics[0]["model_provider"] == "groq"
        assert metrics[0]["model_name"] == "llama-3.3-70b-versatile"
        assert metrics[0]["avg_duration"] == 2.0
        assert metrics[0]["std_duration"] > 0  # Should have std dev
        assert metrics[0]["min_duration"] == 1.0
        assert metrics[0]["max_duration"] == 3.0
        assert metrics[0]["avg_tokens"] == 150.0
        assert metrics[0]["execution_count"] == 3

    def test_excludes_incomplete_executions(self, temp_db: DatabaseConnection) -> None:
        """Test that running/failed executions are excluded."""
        repo = TaskRepository(temp_db)

        # Create task
        task = TaskSubmission(prompt="Test task")
        task_id = repo.create_task(task)

        # Completed execution (should be included)
        exec1 = AgentExecution(
            task_id=task_id, model_provider="groq", model_name="llama-3.3-70b-versatile"
        )
        exec1.mark_completed()
        exec1.duration_seconds = 1.5
        exec1.token_count = 100
        repo.create_execution(exec1)

        # Running execution (should be excluded)
        exec2 = AgentExecution(
            task_id=task_id, model_provider="groq", model_name="llama-3.3-70b-versatile"
        )
        # Don't mark as completed
        repo.create_execution(exec2)

        # Failed execution (should be excluded)
        exec3 = AgentExecution(
            task_id=task_id, model_provider="groq", model_name="llama-3.3-70b-versatile"
        )
        exec3.mark_failed()
        exec3.duration_seconds = 2.0
        repo.create_execution(exec3)

        # Query metrics
        metrics = repo.get_performance_metrics(task_id)

        # Should only include completed execution
        assert len(metrics) == 1
        assert metrics[0]["execution_count"] == 1
        assert metrics[0]["avg_duration"] == 1.5

    def test_all_tasks_aggregation(self, temp_db: DatabaseConnection) -> None:
        """Test metrics aggregation across all tasks."""
        repo = TaskRepository(temp_db)

        # Create two tasks
        task1 = TaskSubmission(prompt="Task 1")
        task1_id = repo.create_task(task1)

        task2 = TaskSubmission(prompt="Task 2")
        task2_id = repo.create_task(task2)

        # Create executions for same model in both tasks
        for task_id in [task1_id, task2_id]:
            execution = AgentExecution(
                task_id=task_id, model_provider="groq", model_name="llama-3.3-70b-versatile"
            )
            execution.mark_completed()
            execution.duration_seconds = 1.5
            execution.token_count = 100
            repo.create_execution(execution)

        # Query all tasks (task_id=None)
        metrics = repo.get_performance_metrics(None)

        # Should aggregate both executions
        assert len(metrics) == 1
        assert metrics[0]["execution_count"] == 2
        assert metrics[0]["avg_duration"] == 1.5

    def test_groups_by_model_correctly(self, temp_db: DatabaseConnection) -> None:
        """Test that different models are grouped separately."""
        repo = TaskRepository(temp_db)

        # Create task
        task = TaskSubmission(prompt="Test task")
        task_id = repo.create_task(task)

        # Create executions for three different models
        models = [
            ("groq", "llama-3.3-70b-versatile"),
            ("groq", "qwen3-32b"),
            ("anthropic", "claude-sonnet-4"),
        ]

        for provider, model_name in models:
            execution = AgentExecution(
                task_id=task_id, model_provider=provider, model_name=model_name
            )
            execution.mark_completed()
            execution.duration_seconds = 1.0
            execution.token_count = 100
            repo.create_execution(execution)

        # Query metrics
        metrics = repo.get_performance_metrics(task_id)

        # Should have 3 separate groups
        assert len(metrics) == 3

        # Verify each model is separate
        model_ids = [(m["model_provider"], m["model_name"]) for m in metrics]
        assert ("anthropic", "claude-sonnet-4") in model_ids
        assert ("groq", "llama-3.3-70b-versatile") in model_ids
        assert ("groq", "qwen3-32b") in model_ids
