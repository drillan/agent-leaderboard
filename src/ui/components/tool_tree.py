"""Tool call hierarchy display component.

This module provides visualization of tool calls made during agent execution,
displaying the call hierarchy and arguments/results.
"""

import json
import logging
from typing import Any

from nicegui import ui

from src.execution.executor import extract_tool_calls

logger = logging.getLogger(__name__)


class ToolCallTree:
    """Display tool calls in a hierarchical tree format.

    Shows:
    - Tool names and call sequence
    - Arguments passed to tools
    - Results returned from tools (if available)
    - Call timing information (if available)
    """

    def __init__(self) -> None:
        """Initialize tool call tree display."""
        self.container: ui.card | None = None
        self.tool_calls: list[dict[str, Any]] = []

    def create(self) -> None:
        """Create the tool call tree UI component."""
        with ui.card().classes("w-full") as card:
            self.container = card
            ui.label("Tool Calls").classes("text-h6")
            ui.label("No tool calls recorded").classes("text-grey-6")

    def update_from_messages(self, messages_json: str | None) -> None:
        """Update tool call tree from execution messages.

        Args:
            messages_json: JSON string of messages from agent execution
        """
        if not messages_json:
            self._render_no_tools()
            return

        try:
            self.tool_calls = extract_tool_calls(messages_json)
        except Exception as e:
            logger.error(f"Failed to extract tool calls: {e}")
            self._render_error(str(e))
            return

        if self.container:
            self.container.clear()

            with self.container:
                ui.label("Tool Calls").classes("text-h6")

                if not self.tool_calls:
                    ui.label("No tool calls made").classes("text-grey-6")
                    return

                # Display each tool call
                for i, tool_call in enumerate(self.tool_calls, 1):
                    self._render_tool_call(i, tool_call)

    def _render_tool_call(self, index: int, tool_call: dict[str, Any]) -> None:
        """Render a single tool call.

        Args:
            index: Tool call sequence number
            tool_call: Tool call information dictionary
        """
        tool_name = tool_call.get("tool_name", "unknown")
        args = tool_call.get("args", {})

        with ui.expansion(f"Tool Call #{index}: {tool_name}").classes("w-full"):
            # Tool name and basic info
            with ui.row().classes("items-center gap-2"):
                ui.icon("build").props("color=blue")
                ui.label(f"Tool: {tool_name}").classes("font-bold")

            # Arguments
            if args:
                ui.label("Arguments:").classes("font-bold text-sm mt-2")
                args_text = json.dumps(args, indent=2)
                ui.code(args_text).classes("w-full")
            else:
                ui.label("No arguments").classes("text-grey-6 text-sm mt-2")

    def _render_no_tools(self) -> None:
        """Render empty state when no messages available."""
        if self.container:
            self.container.clear()

            with self.container:
                ui.label("Tool Calls").classes("text-h6")
                ui.label("No execution data available").classes("text-grey-6")

    def _render_error(self, error_message: str) -> None:
        """Render error state.

        Args:
            error_message: Error description
        """
        if self.container:
            self.container.clear()

            with self.container:
                ui.label("Tool Calls").classes("text-h6")
                ui.label("Error loading tool calls").classes("text-red-6")
                ui.label(error_message).classes("text-grey-7 text-sm")

    def clear(self) -> None:
        """Clear the tool call tree display."""
        self.tool_calls = []
        self._render_no_tools()


def create_tool_call_tree() -> ToolCallTree:
    """Create a tool call tree display component.

    Returns:
        ToolCallTree instance

    Example:
        >>> from src.database.repositories import TaskRepository
        >>> tool_tree = create_tool_call_tree()
        >>> tool_tree.create()
        >>> # Update with messages from execution
        >>> messages_json = '[{"kind":"request","parts":[{"type":"tool_call",...}]}]'
        >>> tool_tree.update_from_messages(messages_json)
    """
    tool_tree = ToolCallTree()
    tool_tree.create()
    return tool_tree
