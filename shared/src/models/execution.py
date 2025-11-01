"""Agent execution domain model.

This module defines the domain model for agent execution attempts.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    """Execution status enumeration.

    Attributes:
        RUNNING: Agent is currently executing
        COMPLETED: Agent finished successfully
        FAILED: Agent encountered an error
        TIMEOUT: Agent exceeded timeout limit
    """

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class AgentExecution(BaseModel):
    """Represents a single agent's attempt to complete a task.

    Attributes:
        id: Primary key (None for new executions)
        task_id: Foreign key to TaskSubmission
        model_provider: AI provider used (openai, anthropic, gemini)
        model_name: Model identifier
        status: Execution status
        started_at: Execution start timestamp
        completed_at: Execution completion timestamp (None if not completed)
        duration_seconds: Execution duration (None if not completed)
        token_count: Total tokens consumed (None if not available)
        all_messages_json: Pydantic AI's all_messages output as JSON string
    """

    id: int | None = None
    task_id: int
    model_provider: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    status: ExecutionStatus = ExecutionStatus.RUNNING
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    token_count: int | None = Field(default=None, ge=0)
    all_messages_json: str | None = None

    def calculate_duration(self) -> None:
        """Calculate and set duration_seconds from timestamps.

        Updates the duration_seconds field based on completed_at - started_at.
        Only calculates if completed_at is set.
        """
        if self.completed_at is not None:
            delta = self.completed_at - self.started_at
            self.duration_seconds = delta.total_seconds()

    def mark_completed(self) -> None:
        """Mark execution as completed and calculate duration."""
        self.status = ExecutionStatus.COMPLETED
        self.completed_at = datetime.now()
        self.calculate_duration()

    def mark_failed(self) -> None:
        """Mark execution as failed and calculate duration."""
        self.status = ExecutionStatus.FAILED
        self.completed_at = datetime.now()
        self.calculate_duration()

    def mark_timeout(self) -> None:
        """Mark execution as timed out and calculate duration."""
        self.status = ExecutionStatus.TIMEOUT
        self.completed_at = datetime.now()
        self.calculate_duration()
