"""Agent response display component.

This module provides UI components for displaying agent responses and execution results.
"""

from nicegui import ui

from src.execution.evaluator import extract_agent_response
from src.models.execution import AgentExecution


class AgentResponseCard:
    """Card component for displaying a single agent's response."""

    def __init__(self, execution: AgentExecution, score: int | None = None):
        """Initialize agent response card.

        Args:
            execution: Agent execution containing response data
            score: Optional evaluation score (0-100)
        """
        self.execution = execution
        self.score = score
        self.container: ui.card | None = None

    def create(self) -> None:
        """Create the agent response card UI component."""
        model_id = f"{self.execution.model_provider}/{self.execution.model_name}"

        with ui.card().classes("w-full") as card:
            self.container = card

            # Header with model name and status
            with ui.row().classes("w-full items-center justify-between"):
                ui.label(model_id).classes("text-subtitle1 font-bold")
                # Status badge
                status_color = {
                    "completed": "green",
                    "failed": "red",
                    "timeout": "orange",
                    "running": "blue",
                }.get(self.execution.status, "grey")
                ui.badge(self.execution.status).props(f"color={status_color}")

            # Score if available
            if self.score is not None:
                score_color = (
                    "green"
                    if self.score >= 80
                    else "orange" if self.score >= 60 else "red"
                )
                with ui.row().classes("w-full"):
                    ui.label("Score: ").classes("font-bold")
                    ui.badge(str(self.score)).props(f"color={score_color}")

            # Separator
            ui.separator().classes("my-3")

            # Agent response text
            response_text = extract_agent_response(self.execution.all_messages_json)

            if response_text:
                ui.label("Response:").classes("font-bold")
                ui.markdown(response_text).classes("w-full text-body2")
            else:
                ui.label("No response available").classes("text-grey-6")

            # Execution details
            with ui.expansion("Details").classes("w-full"):
                with ui.column().classes("w-full gap-2"):
                    if self.execution.duration_seconds is not None:
                        ui.label(
                            f"Duration: {self.execution.duration_seconds:.2f}s"
                        ).classes("text-caption")
                    if self.execution.token_count is not None:
                        ui.label(
                            f"Tokens: {self.execution.token_count}"
                        ).classes("text-caption")
                    if self.execution.completed_at:
                        ui.label(
                            f"Completed: {self.execution.completed_at.isoformat()}"
                        ).classes("text-caption")


class AgentResponsesPanel:
    """Panel component for displaying multiple agent responses."""

    def __init__(
        self, executions: list[AgentExecution] | None = None, scores: dict[int, int] | None = None
    ):
        """Initialize agent responses panel.

        Args:
            executions: List of agent executions to display
            scores: Optional dictionary mapping execution_id to score
        """
        self.executions = executions or []
        self.scores = scores or {}
        self.container: ui.card | None = None
        self.response_cards: list[AgentResponseCard] = []

    def create(self) -> None:
        """Create the agent responses panel UI component."""
        with ui.card().classes("w-full") as card:
            self.container = card
            ui.label("Agent Responses").classes("text-h6")

            if not self.executions:
                ui.label("No executions available").classes("text-grey-6")
                return

            # Create response cards for each execution
            for execution in self.executions:
                score = None
                if execution.id:
                    score = self.scores.get(execution.id)

                response_card = AgentResponseCard(execution, score)
                response_card.create()
                self.response_cards.append(response_card)

    def update_executions(
        self, executions: list[AgentExecution], scores: dict[int, int] | None = None
    ) -> None:
        """Update the panel with new list of executions.

        Args:
            executions: New list of executions
            scores: Optional dictionary mapping execution_id to score
        """
        self.executions = executions
        self.scores = scores or {}
        self.response_cards = []

        if self.container:
            self.container.clear()
            with self.container:
                ui.label("Agent Responses").classes("text-h6")
                self.create()

    def refresh(self) -> None:
        """Refresh the panel display with latest data."""
        if self.container:
            self.container.clear()
            with self.container:
                ui.label("Agent Responses").classes("text-h6")
                self.create()


def create_agent_responses_panel(
    executions: list[AgentExecution] | None = None, scores: dict[int, int] | None = None
) -> AgentResponsesPanel:
    """Create an agent responses panel component.

    Args:
        executions: List of agent executions to display
        scores: Optional dictionary mapping execution_id to score

    Returns:
        AgentResponsesPanel instance

    Example:
        >>> from src.database.connection import DatabaseConnection
        >>> from src.database.repositories import TaskRepository
        >>> db = DatabaseConnection("test.duckdb")
        >>> repo = TaskRepository(db)
        >>> executions = [...]  # List of AgentExecution objects
        >>> panel = create_agent_responses_panel(executions)
        >>> panel.create()
    """
    panel = AgentResponsesPanel(executions, scores)
    panel.create()
    return panel
