"""Execution log display component.

This module provides a UI component for displaying chronological execution logs.
Shows user messages, tool calls, tool responses, and assistant messages in order.
"""

from typing import Any

from nicegui import ui

from src.execution.executor import ExecutionLogEntry, extract_execution_log
from src.models.execution import AgentExecution


def get_message_icon(message_type: str) -> str:
    """Get icon for message type.

    Args:
        message_type: Message type (user, assistant, tool_call, tool_response, etc.)

    Returns:
        Material icon name
    """
    type_lower = message_type.lower()

    if "user" in type_lower:
        return "person"
    elif "assistant" in type_lower or "model" in type_lower:
        return "smart_toy"
    elif "tool_call" in type_lower:
        return "play_arrow"
    elif "tool_response" in type_lower or "tool-response" in type_lower:
        return "check_circle"
    else:
        return "info"


def get_message_color(message_type: str) -> str:
    """Get color for message type.

    Args:
        message_type: Message type

    Returns:
        Tailwind CSS color class
    """
    type_lower = message_type.lower()

    if "user" in type_lower:
        return "blue"
    elif "assistant" in type_lower or "model" in type_lower:
        return "green"
    elif "tool_call" in type_lower:
        return "purple"
    elif "tool_response" in type_lower or "tool-response" in type_lower:
        return "orange"
    else:
        return "grey"


def format_content(content: Any, max_length: int = 300) -> str:
    """Format message content for display.

    Args:
        content: Message content (can be string, dict, or other)
        max_length: Maximum length before truncation

    Returns:
        Formatted content string
    """
    if isinstance(content, dict):
        # Pretty print dict
        import json

        content_str = json.dumps(content, indent=2)
    else:
        content_str = str(content)

    # Truncate if too long
    if len(content_str) > max_length:
        return content_str[:max_length] + "..."

    return content_str


class ExecutionLog:
    """Execution log display component.

    Displays chronological list of execution events.
    """

    def __init__(self, execution: AgentExecution | None = None):
        """Initialize execution log.

        Args:
            execution: Optional agent execution to display log for
        """
        self.execution = execution
        self.container: ui.column | None = None

    def create(self) -> None:
        """Create the execution log UI component."""
        with ui.column().classes("w-full gap-2") as col:
            self.container = col

            if not self.execution:
                ui.label("No execution selected").classes("text-grey-6")
                return

            self._render_log()

    def _render_log(self) -> None:
        """Render execution log entries."""
        if not self.execution:
            return

        # Extract execution log
        try:
            log_entries = extract_execution_log(self.execution)
        except ValueError as e:
            ui.label(f"Failed to extract execution log: {e}").classes("text-red-600")
            return

        if not log_entries:
            ui.label("No messages found in execution").classes("text-grey-6")
            ui.label("The agent may have responded directly without tool calls").classes(
                "text-caption text-grey-7"
            )
            return

        # Render each log entry
        for entry in log_entries:
            self._render_log_entry(entry)

    def _render_log_entry(self, entry: ExecutionLogEntry) -> None:
        """Render a single log entry.

        Args:
            entry: Execution log entry to render
        """
        msg_type = entry["type"]
        content = entry["content"]
        tool_name = entry["tool_name"]
        timestamp = entry["timestamp"]

        # Get styling
        icon = get_message_icon(msg_type)
        color = get_message_color(msg_type)

        # Create entry card
        with ui.card().classes(f"w-full border-l-4 border-{color}-500"):
            with ui.row().classes("w-full items-center gap-2"):
                ui.icon(icon).classes(f"text-{color}-600")

                # Type label
                type_label = msg_type
                if tool_name:
                    type_label = f"{msg_type}: {tool_name}"
                ui.label(type_label).classes(f"font-bold text-{color}-700")

                # Timestamp (if available)
                if timestamp:
                    ui.label(timestamp).classes("text-caption text-grey-6 ml-auto")

            # Content
            content_str = format_content(content)
            with ui.expansion("Content", icon="description").classes("w-full"):
                ui.label(content_str).classes("whitespace-pre-wrap font-mono text-sm")

    def update_execution(self, execution: AgentExecution) -> None:
        """Update the log for a different execution.

        Args:
            execution: New execution to display log for
        """
        self.execution = execution
        if self.container:
            self.container.clear()
            with self.container:
                self._render_log()


def create_execution_log(execution: AgentExecution | None = None) -> ExecutionLog:
    """Create an execution log component.

    Args:
        execution: Optional agent execution to display log for

    Returns:
        ExecutionLog instance

    Example:
        >>> from src.models.execution import AgentExecution, ExecutionStatus
        >>> execution = AgentExecution(
        ...     task_id=1,
        ...     model_provider="openai",
        ...     model_name="gpt-4o",
        ...     status=ExecutionStatus.COMPLETED,
        ... )
        >>> log = create_execution_log(execution)
        >>> log.create()
    """
    log = ExecutionLog(execution)
    log.create()
    return log
