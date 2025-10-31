"""Task submission domain model.

This module defines the domain model for user task submissions.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class TaskSubmission(BaseModel):
    """Represents a user's natural language prompt for task execution.

    Attributes:
        id: Primary key (None for new submissions)
        prompt: Natural language task description
        submitted_at: Submission timestamp
    """

    id: int | None = None
    prompt: str = Field(min_length=1)
    submitted_at: datetime = Field(default_factory=datetime.now)

    @property
    def prompt_trimmed(self) -> str:
        """Get trimmed prompt text.

        Returns:
            Prompt with leading/trailing whitespace removed
        """
        return self.prompt.strip()

    def model_post_init(self, __context: object) -> None:
        """Post-initialization validation.

        Args:
            __context: Pydantic context (unused)

        Raises:
            ValueError: If prompt is empty after trimming
        """
        if not self.prompt_trimmed:
            raise ValueError("Prompt must not be empty after trimming whitespace")
