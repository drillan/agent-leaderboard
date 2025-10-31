"""Tool call tree component.

This module provides a UI component for displaying tool call hierarchies.
Shows tool calls, arguments, results, and nested calls in a tree structure.
"""

from typing import Any

from nicegui import ui
from nicegui.events import ValueChangeEventArguments

from src.execution.executor import ToolCallNode, extract_tool_hierarchy, format_tool_call
from src.models.execution import AgentExecution


def build_tree_structure(nodes: list[ToolCallNode]) -> list[dict[str, Any]]:
    """Build tree structure for NiceGUI ui.tree.

    Args:
        nodes: List of tool call nodes

    Returns:
        Tree structure compatible with ui.tree()
    """
    if not nodes:
        return []

    def node_to_tree(node: ToolCallNode) -> dict[str, Any]:
        """Convert ToolCallNode to ui.tree dict structure."""
        # Format node label
        label = format_tool_call(node, max_result_length=50)

        tree_node: dict[str, Any] = {
            "id": node["call_id"],
            "label": label,
            "icon": "function",
        }

        # Add children recursively
        if node["children"]:
            tree_node["children"] = [node_to_tree(child) for child in node["children"]]

        return tree_node

    return [node_to_tree(node) for node in nodes]


class ToolCallTree:
    """Tool call tree component.

    Displays tool call hierarchy in an expandable tree structure.
    """

    def __init__(self, execution: AgentExecution | None = None):
        """Initialize tool call tree.

        Args:
            execution: Optional agent execution to display tools for
        """
        self.execution = execution
        self.container: ui.card | None = None
        self.tree: ui.tree | None = None

    def create(self) -> None:
        """Create the tool call tree UI component."""
        with ui.card().classes("w-full") as card:
            self.container = card
            ui.label("Tool Calls").classes("text-h6")

            if self.execution:
                self._render_tree()
            else:
                ui.label("No execution selected").classes("text-grey-6")

    def _render_tree(self) -> None:
        """Render tool call tree for the current execution."""
        if not self.execution:
            return

        # Extract tool hierarchy
        try:
            tool_nodes = extract_tool_hierarchy(self.execution)
        except ValueError as e:
            ui.label(f"Failed to extract tool calls: {e}").classes("text-red-600")
            return

        if not tool_nodes:
            ui.label("No tool calls found").classes("text-grey-6")
            return

        # Build tree structure
        tree_data = build_tree_structure(tool_nodes)

        # Create tree
        self.tree = ui.tree(
            nodes=tree_data,
            label_key="label",
            children_key="children",
            node_key="id",
        ).classes("w-full")

        # Expand all nodes by default
        if self.tree:
            self.tree.expand()

    def update_execution(self, execution: AgentExecution) -> None:
        """Update the tree for a different execution.

        Args:
            execution: New execution to display tool calls for
        """
        self.execution = execution
        if self.container:
            self.container.clear()
            with self.container:
                ui.label("Tool Calls").classes("text-h6")
                self._render_tree()

    def refresh(self) -> None:
        """Refresh the tree display with latest data."""
        if self.execution and self.container:
            self.container.clear()
            with self.container:
                ui.label("Tool Calls").classes("text-h6")
                self._render_tree()


class ToolCallTreePanel:
    """Tool call tree panel with execution selector.

    Displays tool calls for a selected execution from a list.
    """

    def __init__(self, executions: list[AgentExecution] | None = None):
        """Initialize tool call tree panel.

        Args:
            executions: Optional list of executions to select from
        """
        self.executions = executions or []
        self.selected_execution: AgentExecution | None = None
        self.container: ui.card | None = None
        self.tree_component: ToolCallTree | None = None

    def _create_ui_content(self) -> None:
        """Create UI content for the tool call tree panel.

        This is used both by create() for initial setup and update_executions()
        for updating with new data.
        """
        if not self.executions:
            ui.label("No executions available").classes("text-grey-6")
            return

        # Create execution selector
        execution_options = {
            f"{exec.model_provider}/{exec.model_name}": exec for exec in self.executions
        }

        # Auto-select first execution if only one is available
        if len(self.executions) == 1:
            first_label = list(execution_options.keys())[0]
            self.selected_execution = execution_options[first_label]

        def on_select(e: ValueChangeEventArguments) -> None:
            selected_label = e.value
            if selected_label and selected_label in execution_options:
                self.selected_execution = execution_options[selected_label]
                if self.tree_component:
                    self.tree_component.update_execution(self.selected_execution)

        # Create selector with auto-selected value if available
        select_widget = ui.select(
            options=list(execution_options.keys()),
            label="Select Execution",
            on_change=on_select,
        ).classes("w-full")

        # Set the default selection if we have a pre-selected execution
        if self.selected_execution:
            default_label = f"{self.selected_execution.model_provider}/{self.selected_execution.model_name}"
            select_widget.value = default_label

        # Create tree component
        self.tree_component = ToolCallTree(self.selected_execution)
        self.tree_component.create()

    def create(self) -> None:
        """Create the tool call tree panel UI component."""
        with ui.card().classes("w-full") as card:
            self.container = card
            ui.label("Tool Call Analysis").classes("text-h6")
            self._create_ui_content()

    def update_executions(self, executions: list[AgentExecution]) -> None:
        """Update the panel with new list of executions.

        Args:
            executions: New list of executions
        """
        self.executions = executions
        self.selected_execution = None
        if self.container:
            self.container.clear()
            with self.container:
                ui.label("Tool Call Analysis").classes("text-h6")
                self._create_ui_content()


def create_tool_call_tree(execution: AgentExecution | None = None) -> ToolCallTree:
    """Create a tool call tree component.

    Args:
        execution: Optional agent execution to display tools for

    Returns:
        ToolCallTree instance

    Example:
        >>> from src.models.execution import AgentExecution, ExecutionStatus
        >>> execution = AgentExecution(
        ...     task_id=1,
        ...     model_provider="openai",
        ...     model_name="gpt-4o",
        ...     status=ExecutionStatus.COMPLETED,
        ... )
        >>> tree = create_tool_call_tree(execution)
        >>> tree.create()
    """
    tree = ToolCallTree(execution)
    tree.create()
    return tree


def create_tool_call_tree_panel(
    executions: list[AgentExecution] | None = None,
) -> ToolCallTreePanel:
    """Create a tool call tree panel with execution selector.

    Args:
        executions: Optional list of executions to select from

    Returns:
        ToolCallTreePanel instance

    Example:
        >>> panel = create_tool_call_tree_panel(executions)
        >>> panel.create()
    """
    panel = ToolCallTreePanel(executions)
    panel.create()
    return panel
