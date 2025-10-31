"""Main task execution page.

This module provides the main UI page for task submission and execution.
"""

import asyncio

from nicegui import ui

from src.agents.eval_agent import create_evaluation_agent
from src.agents.task_agent import create_task_agents_from_config
from src.config.models import AppConfig
from src.database.connection import DatabaseConnection
from src.database.repositories import TaskRepository
from src.execution.executor import evaluate_execution, execute_multi_agent
from src.execution.state import MultiAgentExecutionState
from src.models.execution import AgentExecution
from src.models.task import TaskSubmission
from src.ui.components.input_form import create_task_input_form
from src.ui.components.leaderboard import LeaderboardTable, create_leaderboard_table
from src.ui.components.status_display import (
    ExecutionStatusDisplay,
    create_execution_status_display,
)
from src.ui.components.tool_tree import ToolCallTreePanel, create_tool_call_tree_panel


class MainPage:
    """Main page controller for task execution.

    Handles the integration of input form, execution logic, and status display.
    """

    def __init__(self, config: AppConfig, db: DatabaseConnection):
        """Initialize main page.

        Args:
            config: Application configuration
            db: Database connection
        """
        self.config = config
        self.db = db
        self.repository = TaskRepository(db)
        self.status_display: ExecutionStatusDisplay | None = None
        self.leaderboard: LeaderboardTable | None = None
        self.tool_tree_panel: ToolCallTreePanel | None = None
        self.current_execution_state: MultiAgentExecutionState | None = None
        self.current_task_id: int | None = None
        self.current_executions: list[AgentExecution] = []
        self.is_executing = False

    async def execute_task(self, prompt: str) -> None:
        """Execute a task with multiple agents.

        Args:
            prompt: Task prompt to execute
        """
        if self.is_executing:
            ui.notify("An execution is already in progress", type="warning")
            return

        self.is_executing = True

        try:
            # Create task submission
            task = TaskSubmission(prompt=prompt)
            task_id = self.repository.create_task(task)

            ui.notify(f"Task submitted (ID: {task_id})", type="positive")

            # Create execution state tracker
            self.current_execution_state = MultiAgentExecutionState(task_id=task_id)

            # Add agents to state
            for model_config in self.config.task_agents:
                self.current_execution_state.add_agent(
                    model_config.provider, model_config.model
                )

            # Update status display
            if self.status_display:
                self.status_display.update_state(self.current_execution_state)

            # Create agents
            agents = create_task_agents_from_config(self.config.task_agents)

            # Execute agents in parallel
            executions = await execute_multi_agent(
                agents=agents,
                model_configs=self.config.task_agents,
                prompt=prompt,
                task_id=task_id,
                timeout_seconds=self.config.execution.timeout_seconds,
            )

            # Save execution results to database
            for execution in executions:
                execution_id = self.repository.create_execution(execution)
                execution.id = execution_id

                # Update state
                model_identifier = f"{execution.model_provider}/{execution.model_name}"
                self.current_execution_state.update_status(
                    model_identifier, execution.status
                )

            # Update status display with final results
            if self.status_display:
                self.status_display.update_state(self.current_execution_state)

            # Show completion notification
            completed = self.current_execution_state.get_completed_count()
            failed = self.current_execution_state.get_failed_count()
            total = len(self.config.task_agents)

            ui.notify(
                f"Execution complete: {completed}/{total} succeeded, {failed}/{total} failed",
                type="positive" if completed > 0 else "warning",
            )

            # Run evaluations
            ui.notify("Running evaluations...", type="info")
            evaluation_agent = create_evaluation_agent(self.config.evaluation_agent)

            for execution in executions:
                try:
                    evaluation = await evaluate_execution(
                        evaluation_agent,
                        self.config.evaluation_agent,
                        prompt,
                        execution,
                    )
                    # Save evaluation to database
                    self.repository.create_evaluation(evaluation)
                except Exception as e:
                    model_id = f"{execution.model_provider}/{execution.model_name}"
                    ui.notify(
                        f"Evaluation failed for {model_id}: {e}",
                        type="warning",
                    )

            ui.notify("Evaluations complete!", type="positive")

            # Store current task and executions
            self.current_task_id = task_id
            self.current_executions = executions

            # Refresh leaderboard
            if self.leaderboard:
                self.leaderboard.update_task(task_id)

            # Refresh tool tree panel
            if self.tool_tree_panel:
                self.tool_tree_panel.update_executions(executions)

        except Exception as e:
            ui.notify(f"Execution failed: {str(e)}", type="negative")
            raise

        finally:
            self.is_executing = False

    def create(self) -> None:
        """Create the main page UI."""
        ui.label("Multi-Agent Competition System").classes("text-h4 text-center")

        # Task input form
        def handle_submit(prompt: str) -> None:
            asyncio.create_task(self.execute_task(prompt))

        create_task_input_form(on_submit=handle_submit)

        # Execution status display
        self.status_display = create_execution_status_display(
            self.current_execution_state
        )

        # Leaderboard
        self.leaderboard = create_leaderboard_table(
            self.repository, self.current_task_id
        )

        # Tool call tree panel
        self.tool_tree_panel = create_tool_call_tree_panel(self.current_executions)


def create_main_page(config: AppConfig, db: DatabaseConnection) -> None:
    """Create the main page.

    Args:
        config: Application configuration
        db: Database connection

    Example:
        >>> from src.config.loader import ConfigLoader
        >>> from src.database.connection import DatabaseConnection
        >>> config = ConfigLoader.load("config.toml")
        >>> db = DatabaseConnection("data.duckdb")
        >>> db.initialize_schema()
        >>> create_main_page(config, db)
    """
    page = MainPage(config, db)
    page.create()
