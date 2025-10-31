"""Performance metrics domain model.

This module defines the domain model for agent execution performance metrics.
"""

from pydantic import BaseModel, Field


class PerformanceMetrics(BaseModel):
    """Represents resource consumption data for an agent execution.

    Note: This is a view model derived from AgentExecution data,
    not a separate database entity.

    Attributes:
        execution_id: Foreign key to AgentExecution
        duration_seconds: Execution time in seconds
        token_count: Total tokens used
        model_provider: AI provider name
        model_name: Model identifier
    """

    execution_id: int
    duration_seconds: float = Field(gt=0)
    token_count: int = Field(ge=0)
    model_provider: str = Field(min_length=1)
    model_name: str = Field(min_length=1)

    @property
    def duration_ms(self) -> float:
        """Get duration in milliseconds.

        Returns:
            Duration in milliseconds
        """
        return self.duration_seconds * 1000

    @property
    def tokens_per_second(self) -> float:
        """Calculate tokens processed per second.

        Returns:
            Tokens per second, or 0 if duration is 0
        """
        if self.duration_seconds > 0:
            return self.token_count / self.duration_seconds
        return 0.0

    @property
    def model_identifier(self) -> str:
        """Get full model identifier.

        Returns:
            Combined provider and model name (e.g., "openai/gpt-4o")
        """
        return f"{self.model_provider}/{self.model_name}"
