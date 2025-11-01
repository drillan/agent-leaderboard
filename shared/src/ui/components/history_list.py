"""History list component.

This module provides a UI component for displaying past task execution history.
Shows task prompts, timestamps, execution counts, and scores.
"""

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any, cast

from nicegui import ui

from src.database.repositories import TaskRepository

logger = logging.getLogger(__name__)


def format_timestamp(timestamp: str | datetime | Any) -> str:
    """Format ISO timestamp to human-readable string.

    Args:
        timestamp: ISO format timestamp string or datetime object

    Returns:
        Formatted string (e.g., "2024-01-15 14:30")
    """
    try:
        # If it's already a datetime object, use it directly
        if isinstance(timestamp, datetime):
            dt = timestamp
        else:
            # Otherwise, parse from string
            dt = datetime.fromisoformat(str(timestamp))
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError, TypeError):
        return str(timestamp)


def truncate_prompt(prompt: str, max_length: int = 60) -> str:
    """Truncate prompt text to max length.

    Args:
        prompt: Full prompt text
        max_length: Maximum length before truncation

    Returns:
        Truncated prompt with ellipsis if needed
    """
    if len(prompt) <= max_length:
        return prompt
    return prompt[: max_length - 3] + "..."


class HistoryList:
    """History list component.

    Displays past task submissions in a table with selection support.
    """

    def __init__(
        self,
        repository: TaskRepository,
        on_task_select: Callable[[int], None] | None = None,
    ):
        """Initialize history list.

        Args:
            repository: Task repository for data access
            on_task_select: Optional callback when task is selected (receives task_id)
        """
        self.repository = repository
        self.on_task_select = on_task_select
        self.container: ui.card | None = None
        self.table: ui.table | None = None

    def create(self) -> None:
        """Create the history list UI component."""
        with ui.card().classes("w-full") as card:
            self.container = card
            ui.label("Task Execution History").classes("text-h6")

            self._render_history()

    def _render_history(self) -> None:
        """Render history table."""
        # Query history data
        history_entries = self.repository.get_task_history()
        logger.info(f"_render_history: Rendering {len(history_entries)} history entries")

        if not history_entries:
            logger.info("_render_history: No history entries found")
            ui.label("No task execution history yet").classes("text-grey-6")
            ui.label("Execute a task to get started!").classes("text-caption text-grey-7")
            return

        # Define table columns
        columns = [
            {
                "name": "id",
                "label": "ID",
                "field": "id",
                "align": "center",
                "sortable": True,
            },
            {
                "name": "prompt",
                "label": "Task Prompt",
                "field": "prompt",
                "align": "left",
                "sortable": False,
            },
            {
                "name": "submitted_at",
                "label": "Submitted",
                "field": "submitted_at",
                "align": "center",
                "sortable": True,
            },
            {
                "name": "execution_count",
                "label": "Executions",
                "field": "execution_count",
                "align": "center",
                "sortable": True,
            },
            {
                "name": "highest_score",
                "label": "Best Score",
                "field": "highest_score",
                "align": "center",
                "sortable": True,
            },
        ]

        # Prepare table rows
        rows = []
        for entry in history_entries:
            task_id = cast(int, entry["id"])
            prompt = cast(str, entry["prompt"])
            submitted_at = cast(str, entry["submitted_at"])
            execution_count = cast(int, entry["execution_count"])
            highest_score = entry["highest_score"]  # Can be None

            rows.append(
                {
                    "id": task_id,
                    "prompt": truncate_prompt(prompt),
                    "submitted_at": format_timestamp(submitted_at),
                    "execution_count": execution_count,
                    "highest_score": highest_score if highest_score is not None else "N/A",
                }
            )

        # Create table
        self.table = ui.table(
            columns=columns,
            rows=rows,
            row_key="id",
            selection="single",
        ).classes("w-full")

        # Handle row selection
        if self.on_task_select:

            def on_selection(e: Any) -> None:
                """Handle task selection."""
                selection = e.args["selected"]
                if selection and len(selection) > 0:
                    selected_row = selection[0]
                    task_id = cast(int, selected_row["id"])
                    if self.on_task_select:
                        self.on_task_select(task_id)

            self.table.on("selection", on_selection)

    def refresh(self) -> None:
        """Refresh the history list."""
        logger.info("HistoryList.refresh() called")
        if not self.container:
            logger.warning("HistoryList container is None, cannot refresh")
            return

        # Query history data first to check if there's new data
        history_entries = self.repository.get_task_history()
        logger.info(f"Found {len(history_entries)} history entries in database")

        # Clear table reference
        self.table = None

        # Clear and re-render
        self.container.clear()
        with self.container:
            ui.label("Task Execution History").classes("text-h6")
            self._render_history()
