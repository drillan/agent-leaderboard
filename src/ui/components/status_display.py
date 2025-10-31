"""Execution status display component.

This module provides a UI component for displaying agent execution status.
"""

from nicegui import ui

from src.execution.state import MultiAgentExecutionState
from src.models.execution import ExecutionStatus


def get_status_color(status: ExecutionStatus) -> str:
    """Get color code for execution status.

    Args:
        status: Execution status

    Returns:
        Color name for status display
    """
    color_map = {
        ExecutionStatus.RUNNING: "blue",
        ExecutionStatus.COMPLETED: "green",
        ExecutionStatus.FAILED: "red",
        ExecutionStatus.TIMEOUT: "orange",
    }
    return color_map.get(status, "grey")


def get_status_icon(status: ExecutionStatus) -> str:
    """Get icon name for execution status.

    Args:
        status: Execution status

    Returns:
        Material icon name
    """
    icon_map = {
        ExecutionStatus.RUNNING: "sync",
        ExecutionStatus.COMPLETED: "check_circle",
        ExecutionStatus.FAILED: "error",
        ExecutionStatus.TIMEOUT: "schedule",
    }
    return icon_map.get(status, "help")


class ExecutionStatusDisplay:
    """Reactive execution status display component.

    Displays the current status of all agents in a multi-agent execution.
    Updates automatically when status changes.
    """

    def __init__(self, execution_state: MultiAgentExecutionState | None = None):
        """Initialize status display.

        Args:
            execution_state: Optional initial execution state
        """
        self.execution_state = execution_state
        self.status_labels: dict[str, ui.label] = {}
        self.container: ui.card | None = None

    def create(self) -> None:
        """Create the status display UI component."""
        with ui.card().classes("w-full") as card:
            self.container = card
            ui.label("Execution Status").classes("text-h6")

            if self.execution_state:
                self._render_status()
            else:
                ui.label("No execution in progress").classes("text-grey-6")

    def _render_status(self) -> None:
        """Render status for all agents in the execution state."""
        if not self.execution_state:
            return

        for identifier, agent_state in self.execution_state.agent_states.items():
            with ui.row().classes("items-center gap-2"):
                # Status icon
                icon = get_status_icon(agent_state.status)
                color = get_status_color(agent_state.status)
                ui.icon(icon).props(f"color={color}")

                # Model identifier
                ui.label(identifier).classes("font-bold")

                # Status text
                status_label = ui.label(agent_state.status.value).props(f"color={color}")
                self.status_labels[identifier] = status_label

    def update_state(self, execution_state: MultiAgentExecutionState) -> None:
        """Update the execution state and refresh display.

        Args:
            execution_state: New execution state
        """
        self.execution_state = execution_state

        # Refresh the entire display to ensure all agents are shown
        if self.container:
            self.container.clear()
            with self.container:
                ui.label("Execution Status").classes("text-h6")
                self.status_labels.clear()
                self._render_status()

    def clear(self) -> None:
        """Clear the status display."""
        self.execution_state = None
        self.status_labels.clear()
        if self.container:
            self.container.clear()
            with self.container:
                ui.label("No execution in progress").classes("text-grey-6")


def create_execution_status_display(
    execution_state: MultiAgentExecutionState | None = None,
) -> ExecutionStatusDisplay:
    """Create an execution status display component.

    Args:
        execution_state: Optional initial execution state

    Returns:
        ExecutionStatusDisplay instance

    Example:
        >>> from src.execution.state import MultiAgentExecutionState
        >>> state = MultiAgentExecutionState(task_id=1)
        >>> state.add_agent("openai", "gpt-4o")
        >>> display = create_execution_status_display(state)
        >>> display.create()
    """
    display = ExecutionStatusDisplay(execution_state)
    display.create()
    return display
