"""Leaderboard table component.

This module provides a UI component for displaying agent execution leaderboard.
Shows evaluation scores, rankings, and performance metrics.
"""

from typing import cast

from nicegui import ui

from src.database.repositories import TaskRepository


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
        ]

        # Prepare table rows
        rows = []
        for rank, entry in enumerate(leaderboard_entries, start=1):
            model_identifier = f"{entry['model_provider']}/{entry['model_name']}"
            duration_val = entry.get("duration_seconds")
            duration_seconds = cast(float, duration_val) if duration_val is not None else None
            rows.append(
                {
                    "rank": rank,
                    "model": model_identifier,
                    "score": entry["evaluation_score"],
                    "duration": format_duration(duration_seconds),
                    "tokens": entry.get("token_count") or "N/A",
                    "explanation": entry.get("evaluation_explanation", "N/A"),
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
