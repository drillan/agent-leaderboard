"""Execution state tracking for multi-agent runs.

This module provides state tracking for monitoring agent execution progress.
"""

from dataclasses import dataclass, field

from src.models.execution import ExecutionStatus


@dataclass
class AgentExecutionState:
    """Tracks the execution state of a single agent.

    Attributes:
        model_provider: AI provider (openai, anthropic, gemini)
        model_name: Model identifier
        status: Current execution status
        execution_id: Database ID once created (None before persistence)
    """

    model_provider: str
    model_name: str
    status: ExecutionStatus = ExecutionStatus.RUNNING
    execution_id: int | None = None

    @property
    def model_identifier(self) -> str:
        """Get combined model identifier.

        Returns:
            String in format "provider/model"
        """
        return f"{self.model_provider}/{self.model_name}"


@dataclass
class MultiAgentExecutionState:
    """Tracks the execution state of multiple agents running in parallel.

    Attributes:
        task_id: Database ID of the task being executed
        agent_states: Dictionary mapping model identifier to execution state
    """

    task_id: int
    agent_states: dict[str, AgentExecutionState] = field(default_factory=dict)

    def add_agent(
        self, model_provider: str, model_name: str, execution_id: int | None = None
    ) -> None:
        """Add an agent to the execution state tracker.

        Args:
            model_provider: AI provider name
            model_name: Model identifier
            execution_id: Optional database ID for the execution
        """
        identifier = f"{model_provider}/{model_name}"
        self.agent_states[identifier] = AgentExecutionState(
            model_provider=model_provider,
            model_name=model_name,
            execution_id=execution_id,
        )

    def update_status(self, model_identifier: str, status: ExecutionStatus) -> None:
        """Update the status of a specific agent.

        Args:
            model_identifier: Combined "provider/model" identifier
            status: New execution status

        Raises:
            KeyError: If model_identifier is not found
        """
        if model_identifier not in self.agent_states:
            raise KeyError(f"Unknown agent: {model_identifier}")

        self.agent_states[model_identifier].status = status

    def get_status(self, model_identifier: str) -> ExecutionStatus:
        """Get the current status of a specific agent.

        Args:
            model_identifier: Combined "provider/model" identifier

        Returns:
            Current execution status

        Raises:
            KeyError: If model_identifier is not found
        """
        if model_identifier not in self.agent_states:
            raise KeyError(f"Unknown agent: {model_identifier}")

        return self.agent_states[model_identifier].status

    def all_completed(self) -> bool:
        """Check if all agents have completed (succeeded, failed, or timed out).

        Returns:
            True if all agents are in a terminal state, False otherwise
        """
        terminal_statuses = {
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.TIMEOUT,
        }

        return all(
            state.status in terminal_statuses for state in self.agent_states.values()
        )

    def get_completed_count(self) -> int:
        """Get the number of agents that have completed successfully.

        Returns:
            Count of agents with COMPLETED status
        """
        return sum(
            1
            for state in self.agent_states.values()
            if state.status == ExecutionStatus.COMPLETED
        )

    def get_failed_count(self) -> int:
        """Get the number of agents that have failed or timed out.

        Returns:
            Count of agents with FAILED or TIMEOUT status
        """
        return sum(
            1
            for state in self.agent_states.values()
            if state.status in {ExecutionStatus.FAILED, ExecutionStatus.TIMEOUT}
        )
