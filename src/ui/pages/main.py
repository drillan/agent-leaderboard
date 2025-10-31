"""Main task execution page.

This module provides the main UI page for task submission and execution.
"""

import logging

from nicegui import ui

from src.agents.eval_agent import create_evaluation_agent
from src.agents.task_agent import create_task_agents_from_config
from src.config.models import AppConfig
from src.database.connection import DatabaseConnection
from src.database.repositories import TaskRepository
from src.execution.evaluator import evaluate_execution, extract_agent_response
from src.execution.executor import execute_multi_agent
from src.execution.state import MultiAgentExecutionState
from src.models.execution import ExecutionStatus
from src.models.task import TaskSubmission
from src.ui.components.input_form import create_task_input_form
from src.ui.components.leaderboard import (
    EnhancedLeaderboard,
    create_enhanced_leaderboard,
)
from src.ui.components.status_display import (
    ExecutionStatusDisplay,
    create_execution_status_display,
)
from src.ui.components.tool_tree import ToolCallTree, create_tool_call_tree

logger = logging.getLogger(__name__)


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
        self.current_execution_state: MultiAgentExecutionState | None = None
        self.is_executing = False
        self.leaderboard_component: EnhancedLeaderboard | None = None
        self.tool_tree_component: ToolCallTree | None = None
        self.leaderboard_container: ui.element | None = None
        self.details_container: ui.element | None = None

    async def execute_task(self, prompt: str) -> None:
        """Execute a task with multiple agents.

        Args:
            prompt: Task prompt to execute
        """
        if self.is_executing:
            ui.notify("An execution is already in progress", type="warning")
            return

        self.is_executing = True
        logger.info("Starting task execution")

        try:
            # Create task submission
            task = TaskSubmission(prompt=prompt)
            task_id = self.repository.create_task(task)
            logger.info(f"Task created with ID: {task_id}")

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
            logger.info("Creating agents from config")
            agents = create_task_agents_from_config(self.config.task_agents)

            # Execute agents in parallel
            logger.info(f"Executing {len(agents)} agents in parallel")
            executions = await execute_multi_agent(
                agents=agents,
                model_configs=self.config.task_agents,
                prompt=prompt,
                task_id=task_id,
                timeout_seconds=self.config.execution.timeout_seconds,
            )
            logger.info(f"Agent execution completed: {len(executions)} results")

            # Save execution results to database
            for execution in executions:
                execution_id = self.repository.create_execution(execution)
                execution.id = execution_id

                # Update state
                model_identifier = f"{execution.model_provider}/{execution.model_name}"
                self.current_execution_state.update_status(
                    model_identifier, execution.status
                )
                logger.info(
                    f"Saved execution for {model_identifier}: {execution.status}"
                )

            # Update status display with final results
            if self.status_display:
                self.status_display.update_state(self.current_execution_state)

            # Evaluate completed executions
            logger.info("Running evaluation on completed executions")
            try:
                eval_agent = create_evaluation_agent(
                    self.config.evaluation_agent
                )
                logger.info("Evaluation agent created successfully")
                for execution in executions:
                    if (
                        execution.status == ExecutionStatus.COMPLETED
                        and execution.id is not None
                    ):
                        try:
                            logger.debug(
                                f"Extracting response from execution "
                                f"{execution.id}"
                            )
                            agent_response = extract_agent_response(
                                execution.all_messages_json
                            )
                            logger.debug(
                                f"Extracted response (len={len(agent_response)}): "
                                f"{agent_response[:100] if agent_response else 'EMPTY'}"
                            )
                            if agent_response:
                                logger.info(
                                    f"Evaluating execution {execution.id} "
                                    f"with {len(agent_response)} chars"
                                )
                                evaluation = await evaluate_execution(
                                    execution,
                                    prompt,
                                    agent_response,
                                    eval_agent,
                                    timeout_seconds=30.0,
                                )
                                self.repository.create_evaluation(evaluation)
                                logger.info(
                                    f"Evaluation saved for execution "
                                    f"{execution.id}: score={evaluation.score}"
                                )
                            else:
                                logger.warning(
                                    f"No agent response found for execution "
                                    f"{execution.id}"
                                )
                        except Exception as e:
                            logger.error(
                                f"Failed to evaluate execution "
                                f"{execution.id}: {str(e)}",
                                exc_info=True,
                            )
            except Exception as e:
                logger.error(
                    f"Failed to create evaluation agent: {str(e)}",
                    exc_info=True,
                )

            # Display leaderboard with results
            self._display_leaderboard(task_id)

            # Display tool calls from first execution
            if executions and self.tool_tree_component:
                first_execution = executions[0]
                if first_execution.all_messages_json:
                    logger.info("Updating tool tree with first execution")
                    self.tool_tree_component.update_from_messages(
                        first_execution.all_messages_json
                    )

            # Show completion notification
            completed = self.current_execution_state.get_completed_count()
            failed = self.current_execution_state.get_failed_count()
            total = len(self.config.task_agents)

            logger.info(
                f"Execution complete: {completed}/{total} succeeded, "
                f"{failed}/{total} failed"
            )
            ui.notify(
                f"Execution complete: {completed}/{total} succeeded, {failed}/{total} failed",
                type="positive" if completed > 0 else "warning",
            )

        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}", exc_info=True)
            ui.notify(f"Execution failed: {str(e)}", type="negative")
            raise

        finally:
            self.is_executing = False
            logger.info("Task execution finished")

    def _display_leaderboard(self, task_id: int) -> None:
        """Display leaderboard with execution results.

        Args:
            task_id: Database ID of the task
        """
        try:
            if self.leaderboard_component:
                logger.info(f"Updating leaderboard for task {task_id}")
                self.leaderboard_component.update_leaderboard(task_id)

        except Exception as e:
            logger.error(f"Failed to display leaderboard: {str(e)}", exc_info=True)

    def create(self) -> None:
        """Create the main page UI."""
        ui.label("Multi-Agent Competition System").classes("text-h4 text-center")

        # Create three-column layout: left for input/status, center for leaderboard,
        # right for tool calls
        with ui.row().classes("w-full gap-4"):
            # Left column: Input and Status
            with ui.column().classes("flex-1"):
                # Task input form
                async def handle_submit(prompt: str) -> None:
                    await self.execute_task(prompt)

                create_task_input_form(on_submit=handle_submit)

                # Execution status display
                self.status_display = create_execution_status_display(
                    self.current_execution_state
                )

            # Center column: Enhanced Leaderboard
            with ui.column().classes("flex-1"):
                self.leaderboard_component = create_enhanced_leaderboard(self.db)

            # Right column: Tool Calls (optional detailed view)
            with ui.column().classes("flex-1"):
                self.tool_tree_component = create_tool_call_tree()


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
