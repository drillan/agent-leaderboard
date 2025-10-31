"""Enhanced leaderboard component for displaying evaluation results.

This module provides a leaderboard component with color-coded scores,
evaluation explanations, and detailed result visualization.
"""

from nicegui import ui

from src.database.connection import DatabaseConnection
from src.database.repositories import TaskRepository
from src.execution.evaluator import extract_agent_response


def get_score_color(score: int | None) -> str:
    """Get color for score display based on value.

    Args:
        score: Score value (0-100) or None

    Returns:
        Color name for score display
    """
    if score is None:
        return "grey"
    if score >= 80:
        return "green"
    elif score >= 60:
        return "amber"
    elif score >= 40:
        return "orange"
    else:
        return "red"


def get_score_badge_icon(score: int | None) -> str:
    """Get icon for score badge.

    Args:
        score: Score value (0-100) or None

    Returns:
        Material icon name
    """
    if score is None:
        return "help"
    if score >= 90:
        return "star"
    elif score >= 80:
        return "check_circle"
    elif score >= 60:
        return "thumb_up"
    else:
        return "warning"


class EnhancedLeaderboard:
    """Enhanced leaderboard display with detailed score and evaluation info.

    Displays agent execution results with:
    - Color-coded scores (green/yellow/orange/red)
    - Evaluation explanations
    - Performance metrics (duration, tokens)
    - Visual badges and icons
    """

    def __init__(self, db: DatabaseConnection):
        """Initialize leaderboard.

        Args:
            db: Database connection
        """
        self.db = db
        self.repository = TaskRepository(db)
        self.container: ui.card | None = None

    def create(self) -> None:
        """Create the leaderboard UI component."""
        with ui.card().classes("w-full") as card:
            self.container = card
            ui.label("Leaderboard").classes("text-h6")
            ui.label("No execution yet").classes("text-grey-6")

    def update_leaderboard(self, task_id: int) -> None:
        """Update leaderboard with task results.

        Args:
            task_id: Database ID of the task
        """
        try:
            leaderboard: list[dict[str, object]] = (
                self.repository.get_leaderboard(task_id)
            )

            if not self.container:
                return

            self.container.clear()

            with self.container:
                ui.label("Leaderboard").classes("text-h6")

                if not leaderboard:
                    ui.label("No results available").classes("text-grey-6")
                    return

                # Display results as cards with details
                for i, entry in enumerate(leaderboard, 1):
                    self._render_result_card(i, entry)

        except Exception as e:
            if self.container:
                self.container.clear()
                with self.container:
                    ui.label("Error loading leaderboard").classes("text-h6")
                    ui.label(f"Failed to display results: {str(e)}").classes(
                        "text-red-6"
                    )

    def _render_result_card(
        self, rank: int, entry: dict[str, object]
    ) -> None:
        """Render a single result card.

        Args:
            rank: Ranking position (1, 2, 3, etc.)
            entry: Leaderboard entry dictionary
        """
        score_obj = entry.get("score")
        score: int | None = (
            int(score_obj) if isinstance(score_obj, (int, float)) else None
        )
        score_color = get_score_color(score)
        score_icon = get_score_badge_icon(score)

        with ui.card().classes("w-full"):
            # Header row: Rank, Model, Score
            with ui.row().classes("w-full items-center gap-4"):
                # Rank badge
                with ui.badge(f"#{rank}").props("color=blue"):
                    pass

                # Model info
                with ui.column().classes("flex-1"):
                    model_name = entry.get("model_name", "N/A")
                    provider = entry.get("model_provider", "N/A")
                    ui.label(f"{provider}/{model_name}").classes("font-bold")

                # Score badge with icon
                if score is not None:
                    with ui.row().classes("items-center gap-2"):
                        ui.icon(score_icon).props(f"color={score_color} size=lg")
                        ui.label(f"{score}/100").classes(f"text-{score_color} font-bold text-lg")
                else:
                    ui.label("N/A").classes("text-grey-6")

            ui.separator().classes("my-2")

            # Details row
            with ui.row().classes("w-full gap-8 text-sm"):
                # Status
                status_obj = entry.get("status", "N/A")
                status: str = str(status_obj) if status_obj else "N/A"
                status_color = (
                    "green" if status == "completed" else
                    "orange" if status == "timeout" else
                    "red" if status == "failed" else
                    "grey"
                )
                with ui.column().classes("flex-0"):
                    ui.label("Status").classes("font-bold")
                    ui.label(status).props(f"color={status_color}")

                # Duration
                duration = entry.get("duration_seconds")
                duration_text = (
                    f"{duration:.2f}s"
                    if isinstance(duration, (int, float))
                    else "N/A"
                )
                with ui.column().classes("flex-0"):
                    ui.label("Duration").classes("font-bold")
                    ui.label(duration_text)

                # Token count
                tokens = entry.get("token_count", 0)
                with ui.column().classes("flex-0"):
                    ui.label("Tokens").classes("font-bold")
                    ui.label(str(tokens))

            # Agent Response section
            all_messages = entry.get("all_messages")
            agent_response = ""
            if all_messages:
                try:
                    agent_response = extract_agent_response(str(all_messages))
                except Exception:
                    agent_response = ""

            if agent_response:
                ui.separator().classes("my-2")
                ui.label("Agent Response").classes("font-bold text-sm")
                ui.label(agent_response).classes(
                    "text-sm text-blue-7 whitespace-normal"
                )

            # Explanation section
            explanation_obj = entry.get("evaluation_text")
            explanation: str | None = (
                str(explanation_obj) if explanation_obj else None
            )
            if explanation:
                ui.separator().classes("my-2")
                ui.label("Evaluation").classes("font-bold text-sm")
                ui.label(explanation).classes("text-sm text-grey-7 whitespace-normal")


def create_enhanced_leaderboard(db: DatabaseConnection) -> EnhancedLeaderboard:
    """Create an enhanced leaderboard component.

    Args:
        db: Database connection

    Returns:
        EnhancedLeaderboard instance

    Example:
        >>> from src.database.connection import DatabaseConnection
        >>> db = DatabaseConnection("data.duckdb")
        >>> leaderboard = create_enhanced_leaderboard(db)
        >>> leaderboard.create()
        >>> leaderboard.update_leaderboard(task_id=1)
    """
    leaderboard = EnhancedLeaderboard(db)
    leaderboard.create()
    return leaderboard
