"""Evaluation result domain model.

This module defines the domain model for agent execution evaluations.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    """Represents the evaluation agent's assessment of an agent execution.

    Attributes:
        id: Primary key (None for new evaluations)
        execution_id: Foreign key to AgentExecution
        score: Numeric score from 0 to 100 (inclusive)
        explanation: Text explanation of the score
        evaluated_at: Evaluation timestamp
    """

    id: int | None = None
    execution_id: int
    score: int = Field(ge=0, le=100)
    explanation: str = Field(min_length=1)
    evaluated_at: datetime = Field(default_factory=datetime.now)

    @property
    def explanation_trimmed(self) -> str:
        """Get trimmed explanation text.

        Returns:
            Explanation with leading/trailing whitespace removed
        """
        return self.explanation.strip()

    def model_post_init(self, __context: object) -> None:
        """Post-initialization validation.

        Args:
            __context: Pydantic context (unused)

        Raises:
            ValueError: If explanation is empty after trimming
        """
        if not self.explanation_trimmed:
            raise ValueError("Explanation must not be empty after trimming whitespace")

    @property
    def is_passing(self) -> bool:
        """Check if the score is passing (>= 50).

        Returns:
            True if score is 50 or above, False otherwise
        """
        return self.score >= 50

    @property
    def grade(self) -> str:
        """Get letter grade based on score.

        Returns:
            Letter grade (A, B, C, D, F)
        """
        if self.score >= 90:
            return "A"
        elif self.score >= 80:
            return "B"
        elif self.score >= 70:
            return "C"
        elif self.score >= 60:
            return "D"
        else:
            return "F"
