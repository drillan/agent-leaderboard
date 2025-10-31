"""Leaderboard table component.

This module provides a UI component for displaying agent execution leaderboard.
Shows evaluation scores, rankings, and performance metrics.
"""

from typing import Any, cast

from nicegui import ui

from src.database.repositories import TaskRepository
from src.ui.components.execution_log import create_execution_log


def format_duration(seconds: float | None) -> str:
    """Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "5.2s", "N/A")
    """
    if seconds is None:
        return "N/A"
    return f"{seconds:.2f}s"


def get_score_color(score: int) -> str:
    """Get color for score display based on value.

    Args:
        score: Score value (0-100)

    Returns:
        Color name for score display
    """
    if score >= 90:
        return "green"
    elif score >= 80:
        return "light-green"
    elif score >= 70:
        return "yellow"
    elif score >= 60:
        return "orange"
    else:
        return "red"


def get_grade_icon(score: int) -> str:
    """Get icon for grade display.

    Args:
        score: Score value (0-100)

    Returns:
        Material icon name
    """
    if score >= 90:
        return "emoji_events"  # Trophy
    elif score >= 80:
        return "thumb_up"
    elif score >= 70:
        return "check"
    elif score >= 60:
        return "remove"
    else:
        return "thumb_down"


class LeaderboardTable:
    """Leaderboard table component.

    Displays evaluation results for a task in a sortable table.
    """

    def __init__(self, repository: TaskRepository, task_id: int | None = None):
        """Initialize leaderboard table.

        Args:
            repository: Task repository for data access
            task_id: Optional task ID to display leaderboard for
        """
        self.repository = repository
        self.task_id = task_id
        self.container: ui.card | None = None
        self.table: ui.table | None = None

    def create(self) -> None:
        """Create the leaderboard table UI component."""
        with ui.card().classes("w-full") as card:
            self.container = card
            ui.label("Leaderboard").classes("text-h6")

            if self.task_id:
                self._render_leaderboard()
            else:
                ui.label("No task selected").classes("text-grey-6")

    def _render_leaderboard(self) -> None:
        """Render leaderboard table for the current task."""
        if not self.task_id:
            return

        # Query leaderboard data
        leaderboard_entries = self.repository.get_leaderboard(self.task_id)

        if not leaderboard_entries:
            ui.label("No evaluations available yet").classes("text-grey-6")
            return

        # Define table columns
        columns = [
            {
                "name": "rank",
                "label": "Rank",
                "field": "rank",
                "align": "center",
                "sortable": False,
            },
            {
                "name": "model",
                "label": "Model",
                "field": "model",
                "align": "left",
                "sortable": True,
            },
            {
                "name": "score",
                "label": "Score",
                "field": "score",
                "align": "center",
                "sortable": True,
            },
            {
                "name": "duration",
                "label": "Duration",
                "field": "duration",
                "align": "center",
                "sortable": True,
            },
            {
                "name": "tokens",
                "label": "Tokens",
                "field": "tokens",
                "align": "center",
                "sortable": True,
            },
            {
                "name": "explanation",
                "label": "Explanation",
                "field": "explanation",
                "align": "left",
                "sortable": False,
            },
            {
                "name": "actions",
                "label": "Actions",
                "field": "actions",
                "align": "center",
                "sortable": False,
            },
        ]

        # Prepare table rows
        rows = []
        for rank, entry in enumerate(leaderboard_entries, start=1):
            model_identifier = f"{entry['model_provider']}/{entry['model_name']}"
            duration_val = entry.get("duration_seconds")
            duration_seconds = cast(float, duration_val) if duration_val is not None else None
            execution_id = cast(int, entry["execution_id"])
            rows.append(
                {
                    "rank": rank,
                    "model": model_identifier,
                    "score": entry["evaluation_score"],
                    "duration": format_duration(duration_seconds),
                    "tokens": entry.get("token_count") or "N/A",
                    "explanation": entry.get("evaluation_explanation", "N/A"),
                    "execution_id": execution_id,
                    "actions": "",  # Placeholder for actions column
                }
            )

        # Create table
        self.table = ui.table(
            columns=columns,
            rows=rows,
            row_key="rank",
        ).classes("w-full")

        # Add custom styling for score column
        self.table.add_slot(
            "body-cell-score",
            r"""
            <q-td :props="props">
                <q-badge :color="props.row.score >= 90 ? 'green' :
                                 props.row.score >= 80 ? 'light-green' :
                                 props.row.score >= 70 ? 'yellow' :
                                 props.row.score >= 60 ? 'orange' : 'red'">
                    {{ props.row.score }}
                </q-badge>
            </q-td>
            """,
        )

        # Add custom styling for rank column
        self.table.add_slot(
            "body-cell-rank",
            r"""
            <q-td :props="props">
                <div class="text-center">
                    <q-icon v-if="props.row.rank === 1"
                            name="emoji_events" color="gold" size="sm" />
                    <q-icon v-else-if="props.row.rank === 2"
                            name="emoji_events" color="silver" size="sm" />
                    <q-icon v-else-if="props.row.rank === 3"
                            name="emoji_events" color="brown" size="sm" />
                    <span v-else>{{ props.row.rank }}</span>
                </div>
            </q-td>
            """,
        )

        # Add actions column with view log button
        self.table.add_slot(
            "body-cell-actions",
            r"""
            <q-td :props="props">
                <q-btn
                    flat dense round
                    icon="visibility"
                    color="primary"
                    @click="$parent.$emit('view_log', props.row.execution_id)"
                >
                    <q-tooltip>View Execution Log</q-tooltip>
                </q-btn>
            </q-td>
            """,
        )

        # Handle view log button clicks
        def on_view_log(e: Any) -> None:
            """Handle view log button click."""
            execution_id = e.args
            if execution_id is not None:
                self._show_execution_log_modal(execution_id)

        self.table.on("view_log", on_view_log)

    def _show_execution_log_modal(self, execution_id: int) -> None:
        """Show execution log modal for the given execution.

        Args:
            execution_id: ID of the execution to show log for
        """
        # Fetch execution from database
        execution = self.repository.get_execution(execution_id)

        if not execution:
            ui.notify("Execution not found", type="negative")
            return

        # Create modal dialog
        with ui.dialog() as dialog, ui.card().classes("w-full max-w-4xl"):
            ui.label(f"Execution Log: {execution.model_provider}/{execution.model_name}").classes(
                "text-h6"
            )
            ui.label(f"Status: {execution.status}").classes("text-caption text-grey-7")

            # Create execution log component
            create_execution_log(execution)

            # Close button
            with ui.row().classes("w-full justify-end mt-4"):
                ui.button("Close", on_click=dialog.close).props("outline")

        dialog.open()

    def update_task(self, task_id: int) -> None:
        """Update the leaderboard for a different task.

        Args:
            task_id: New task ID to display leaderboard for
        """
        self.task_id = task_id
        if self.container:
            self.container.clear()
            with self.container:
                ui.label("Leaderboard").classes("text-h6")
                self._render_leaderboard()

    def refresh(self) -> None:
        """Refresh the leaderboard display with latest data."""
        if self.task_id and self.container:
            self.container.clear()
            with self.container:
                ui.label("Leaderboard").classes("text-h6")
                self._render_leaderboard()


def create_leaderboard_table(
    repository: TaskRepository, task_id: int | None = None
) -> LeaderboardTable:
    """Create a leaderboard table component.

    Args:
        repository: Task repository for data access
        task_id: Optional task ID to display leaderboard for

    Returns:
        LeaderboardTable instance

    Example:
        >>> from src.database.connection import DatabaseConnection
        >>> from src.database.repositories import TaskRepository
        >>> db = DatabaseConnection("test.duckdb")
        >>> repo = TaskRepository(db)
        >>> leaderboard = create_leaderboard_table(repo, task_id=1)
        >>> leaderboard.create()
    """
    leaderboard = LeaderboardTable(repository, task_id)
    leaderboard.create()
    return leaderboard
