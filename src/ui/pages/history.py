"""History page.

This module provides the task execution history page with
historical leaderboard viewing.
"""

from nicegui import ui

from src.config.models import AppConfig
from src.database.connection import DatabaseConnection
from src.database.repositories import TaskRepository
from src.ui.components.history_list import HistoryList
from src.ui.components.leaderboard import LeaderboardTable


class HistoryPage:
    """History page controller.

    Displays past task executions and their historical leaderboards.
    """

    def __init__(self, config: AppConfig, db: DatabaseConnection):
        """Initialize history page.

        Args:
            config: Application configuration
            db: Database connection
        """
        self.config = config
        self.db = db
        self.repository = TaskRepository(db)
        self.history_list: HistoryList | None = None
        self.leaderboard: LeaderboardTable | None = None
        self.leaderboard_container: ui.card | None = None
        self.current_task_id: int | None = None

    def create(self) -> None:
        """Create the history page UI."""
        ui.label("Task Execution History").classes("text-h4 text-center")
        ui.label("Browse past executions and view historical leaderboards").classes(
            "text-subtitle2 text-center text-grey-7"
        )

        # History list
        self.history_list = HistoryList(
            repository=self.repository, on_task_select=self._on_task_select
        )
        self.history_list.create()

        # Leaderboard container (initially empty)
        with ui.card().classes("w-full") as card:
            self.leaderboard_container = card
            ui.label("Historical Leaderboard").classes("text-h6")
            ui.label("Select a task from the history to view its leaderboard").classes(
                "text-grey-6"
            )

    def _on_task_select(self, task_id: int) -> None:
        """Handle task selection from history list.

        Args:
            task_id: ID of selected task
        """
        self.current_task_id = task_id

        # Clear and rebuild leaderboard container
        if self.leaderboard_container:
            self.leaderboard_container.clear()
            with self.leaderboard_container:
                ui.label("Historical Leaderboard").classes("text-h6")

                # Get task info
                task = self.repository.get_task(task_id)
                if task:
                    ui.label(f"Task #{task_id}: {task.prompt}").classes(
                        "text-caption text-grey-7"
                    )

                # Render leaderboard for selected task
                self.leaderboard = LeaderboardTable(
                    repository=self.repository, task_id=task_id
                )
                self.leaderboard.create()

    def refresh(self) -> None:
        """Refresh the history page with latest data."""
        if self.history_list:
            self.history_list.refresh()
        if self.leaderboard and self.current_task_id:
            self.leaderboard.update_task(self.current_task_id)


def create_history_page(config: AppConfig, db: DatabaseConnection) -> None:
    """Create the history page.

    Args:
        config: Application configuration
        db: Database connection

    Example:
        >>> from src.config.loader import ConfigLoader
        >>> from src.database.connection import DatabaseConnection
        >>> config = ConfigLoader.load("config.toml")
        >>> db = DatabaseConnection("data.duckdb")
        >>> db.initialize_schema()
        >>> create_history_page(config, db)
    """
    page = HistoryPage(config, db)
    page.create()
