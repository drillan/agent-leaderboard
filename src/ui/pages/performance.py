"""Performance dashboard page.

This module provides the performance metrics dashboard page with
duration and token consumption charts.
"""

import logging
from typing import cast

from nicegui import ui
from nicegui.events import ValueChangeEventArguments

from src.config.models import AppConfig
from src.database.connection import DatabaseConnection
from src.database.repositories import TaskRepository
from src.ui.components.charts import PerformanceCharts, create_performance_charts

logger = logging.getLogger(__name__)


class PerformancePage:
    """Performance dashboard page controller.

    Displays performance metrics charts for agent executions.
    """

    def __init__(self, config: AppConfig, db: DatabaseConnection):
        """Initialize performance page.

        Args:
            config: Application configuration
            db: Database connection
        """
        self.config = config
        self.db = db
        self.repository = TaskRepository(db)
        self.charts: PerformanceCharts | None = None
        self.task_selector: ui.select | None = None
        self.current_task_id: int | None = None

    def create(self) -> None:
        """Create the performance page UI."""
        ui.label("Performance Dashboard").classes("text-h4 text-center")
        ui.label("Analyze execution duration and token consumption metrics").classes(
            "text-subtitle2 text-center text-grey-7"
        )

        # Task selector
        with ui.card().classes("w-full"):
            ui.label("Filter by Task").classes("text-h6")

            # Get all tasks for selector
            tasks = self._get_all_tasks()

            if not tasks:
                ui.label("No tasks available yet").classes("text-grey-6")
                return

            task_options: dict[str, int | None] = {"All Tasks": None}
            for task in tasks:
                prompt_str = cast(str, task["prompt"])
                task_id = cast(int, task["id"])
                prompt_preview = prompt_str[:50] + "..." if len(prompt_str) > 50 else prompt_str
                task_options[f"Task #{task_id}: {prompt_preview}"] = task_id

            def on_task_select(e: ValueChangeEventArguments) -> None:
                selected_label = e.value
                if selected_label and selected_label in task_options:
                    self.current_task_id = task_options[selected_label]
                    if self.charts:
                        self.charts.update_task(self.current_task_id)

            self.task_selector = ui.select(
                options=list(task_options.keys()),
                label="Select Task",
                value="All Tasks",
                on_change=on_task_select,
            ).classes("w-full")

        # Performance charts
        self.charts = create_performance_charts(self.repository, self.current_task_id)

    def _get_all_tasks(self) -> list[dict[str, object]]:
        """Get all task submissions from database.

        Returns:
            List of task dictionaries with id and prompt
        """
        conn = self.db.connect()
        results = conn.execute(
            """
            SELECT id, prompt
            FROM task_submissions
            ORDER BY id DESC
            """
        ).fetchall()

        tasks = []
        for row in results:
            tasks.append({"id": row[0], "prompt": row[1]})

        return tasks

    def refresh(self) -> None:
        """Refresh the performance page with latest data."""
        logger.info("PerformancePage.refresh() called")
        if self.charts:
            logger.info("Charts exist, calling charts.refresh()")
            self.charts.refresh()
        else:
            logger.warning("Charts is None, cannot refresh")


def create_performance_page(config: AppConfig, db: DatabaseConnection) -> None:
    """Create the performance dashboard page.

    Args:
        config: Application configuration
        db: Database connection

    Example:
        >>> from src.config.loader import ConfigLoader
        >>> from src.database.connection import DatabaseConnection
        >>> config = ConfigLoader.load("config.toml")
        >>> db = DatabaseConnection("data.duckdb")
        >>> db.initialize_schema()
        >>> create_performance_page(config, db)
    """
    page = PerformancePage(config, db)
    page.create()
