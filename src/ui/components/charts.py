"""Performance charts components.

This module provides UI components for visualizing performance metrics
using Plotly charts via NiceGUI's ui.plotly() integration.
"""

import logging
from typing import Any

import plotly.graph_objects as go  # type: ignore[import-untyped]
from nicegui import ui

from src.database.repositories import TaskRepository

logger = logging.getLogger(__name__)


def create_duration_chart(metrics: list[dict[str, Any]]) -> go.Figure:
    """Create a bar chart for execution durations with error bars.

    Args:
        metrics: List of aggregated performance metrics dictionaries

    Returns:
        Plotly Figure with duration bar chart and error bars
    """
    if not metrics:
        # Return empty chart with message
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"size": 20, "color": "gray"},
        )
        fig.update_layout(
            title="Execution Duration by Model (Average ± Std Dev)",
            xaxis={"visible": False},
            yaxis={"visible": False},
        )
        return fig

    # Extract data
    models = [f"{m['model_provider']}/{m['model_name']}" for m in metrics]
    avg_durations = [float(m["avg_duration"]) for m in metrics]
    std_durations = [float(m["std_duration"]) for m in metrics]
    counts = [int(m["execution_count"]) for m in metrics]

    # Create hover text with detailed statistics
    hover_texts = [
        f"Average: {avg:.2f}s<br>"
        f"Std Dev: {std:.2f}s<br>"
        f"Min: {m['min_duration']:.2f}s<br>"
        f"Max: {m['max_duration']:.2f}s<br>"
        f"Executions: {count}"
        for avg, std, count, m in zip(avg_durations, std_durations, counts, metrics, strict=True)
    ]

    # Create bar chart with error bars
    fig = go.Figure(
        data=[
            go.Bar(
                x=models,
                y=avg_durations,
                error_y={"type": "data", "array": std_durations, "visible": True},
                marker={"color": "skyblue"},
                text=[f"{d:.2f}s (n={c})" for d, c in zip(avg_durations, counts, strict=True)],
                textposition="outside",
                hovertext=hover_texts,
                hoverinfo="text",
            )
        ]
    )

    fig.update_layout(
        title="Execution Duration by Model (Average ± Std Dev)",
        xaxis_title="Model",
        yaxis_title="Duration (seconds)",
        hovermode="x unified",
        showlegend=False,
    )

    return fig


def create_token_chart(metrics: list[dict[str, Any]]) -> go.Figure:
    """Create a bar chart for token consumption with error bars.

    Args:
        metrics: List of aggregated performance metrics dictionaries

    Returns:
        Plotly Figure with token bar chart and error bars
    """
    if not metrics:
        # Return empty chart with message
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"size": 20, "color": "gray"},
        )
        fig.update_layout(
            title="Token Consumption by Model (Average ± Std Dev)",
            xaxis={"visible": False},
            yaxis={"visible": False},
        )
        return fig

    # Extract data
    models = [f"{m['model_provider']}/{m['model_name']}" for m in metrics]
    avg_tokens = [float(m["avg_tokens"]) for m in metrics]
    std_tokens = [float(m["std_tokens"]) for m in metrics]
    counts = [int(m["execution_count"]) for m in metrics]

    # Create hover text with detailed statistics
    hover_texts = [
        f"Average: {avg:.0f} tokens<br>Std Dev: {std:.0f}<br>Executions: {count}"
        for avg, std, count in zip(avg_tokens, std_tokens, counts, strict=True)
    ]

    # Create bar chart with error bars
    fig = go.Figure(
        data=[
            go.Bar(
                x=models,
                y=avg_tokens,
                error_y={"type": "data", "array": std_tokens, "visible": True},
                marker={"color": "lightgreen"},
                text=[f"{int(t)} (n={c})" for t, c in zip(avg_tokens, counts, strict=True)],
                textposition="outside",
                hovertext=hover_texts,
                hoverinfo="text",
            )
        ]
    )

    fig.update_layout(
        title="Token Consumption by Model (Average ± Std Dev)",
        xaxis_title="Model",
        yaxis_title="Tokens",
        hovermode="x unified",
        showlegend=False,
    )

    return fig


def create_tokens_per_second_chart(metrics: list[dict[str, Any]]) -> go.Figure:
    """Create a bar chart for tokens per second (throughput).

    Args:
        metrics: List of aggregated performance metrics dictionaries

    Returns:
        Plotly Figure with tokens/sec bar chart
    """
    if not metrics:
        # Return empty chart with message
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"size": 20, "color": "gray"},
        )
        fig.update_layout(
            title="Throughput by Model (Average)",
            xaxis={"visible": False},
            yaxis={"visible": False},
        )
        return fig

    # Extract data and calculate average tokens per second
    models = [f"{m['model_provider']}/{m['model_name']}" for m in metrics]
    avg_throughput = []
    counts = [int(m["execution_count"]) for m in metrics]

    for m in metrics:
        avg_duration = float(m["avg_duration"])
        avg_tokens = float(m["avg_tokens"])
        tokens_per_sec = avg_tokens / avg_duration if avg_duration > 0 else 0
        avg_throughput.append(tokens_per_sec)

    # Create hover text with detailed statistics
    hover_texts = [
        f"Throughput: {tps:.1f} tokens/s<br>"
        f"Avg Duration: {m['avg_duration']:.2f}s<br>"
        f"Avg Tokens: {m['avg_tokens']:.0f}<br>"
        f"Executions: {count}"
        for tps, count, m in zip(avg_throughput, counts, metrics, strict=True)
    ]

    # Create bar chart
    fig = go.Figure(
        data=[
            go.Bar(
                x=models,
                y=avg_throughput,
                marker={"color": "coral"},
                text=[f"{t:.1f} (n={c})" for t, c in zip(avg_throughput, counts, strict=True)],
                textposition="outside",
                hovertext=hover_texts,
                hoverinfo="text",
            )
        ]
    )

    fig.update_layout(
        title="Throughput by Model (Average Tokens/Second)",
        xaxis_title="Model",
        yaxis_title="Tokens per Second",
        hovermode="x unified",
        showlegend=False,
    )

    return fig


class PerformanceCharts:
    """Performance charts component.

    Displays multiple performance charts (duration, tokens, throughput).
    """

    def __init__(self, repository: TaskRepository, task_id: int | None = None):
        """Initialize performance charts.

        Args:
            repository: Task repository for data access
            task_id: Optional task ID to filter metrics. If None, shows all tasks.
        """
        self.repository = repository
        self.task_id = task_id
        self.container: ui.card | None = None
        self.duration_plot: ui.plotly | None = None
        self.token_plot: ui.plotly | None = None
        self.throughput_plot: ui.plotly | None = None

    def create(self) -> None:
        """Create the performance charts UI component."""
        with ui.card().classes("w-full") as card:
            self.container = card
            ui.label("Performance Metrics").classes("text-h6")

            # Query metrics
            metrics = self.repository.get_performance_metrics(self.task_id)

            if not metrics:
                ui.label("No performance data available").classes("text-grey-6")
                return

            # Create charts
            with ui.row().classes("w-full gap-4"):
                with ui.column().classes("flex-1"):
                    duration_fig = create_duration_chart(metrics)
                    self.duration_plot = ui.plotly(duration_fig).classes("w-full")

                with ui.column().classes("flex-1"):
                    token_fig = create_token_chart(metrics)
                    self.token_plot = ui.plotly(token_fig).classes("w-full")

            # Throughput chart (full width)
            throughput_fig = create_tokens_per_second_chart(metrics)
            self.throughput_plot = ui.plotly(throughput_fig).classes("w-full")

    def update_task(self, task_id: int | None) -> None:
        """Update charts for a different task.

        Args:
            task_id: New task ID to display metrics for, or None for all tasks
        """
        self.task_id = task_id
        if self.container:
            self.container.clear()
            with self.container:
                ui.label("Performance Metrics").classes("text-h6")
                self.create()

    def refresh(self) -> None:
        """Refresh the charts with latest data."""
        logger.info("PerformanceCharts.refresh() called")
        if self.container:
            logger.info(f"Container exists, clearing and re-rendering for task_id={self.task_id}")
            self.container.clear()
            with self.container:
                ui.label("Performance Metrics").classes("text-h6")

                # Query metrics
                metrics = self.repository.get_performance_metrics(self.task_id)
                logger.info(f"Retrieved {len(metrics)} performance metrics from database")

                if not metrics:
                    logger.warning("No performance metrics found, showing empty message")
                    ui.label("No performance data available").classes("text-grey-6")
                    return

                logger.info(f"Creating charts for {len(metrics)} metrics")
                # Recreate charts
                with ui.row().classes("w-full gap-4"):
                    with ui.column().classes("flex-1"):
                        duration_fig = create_duration_chart(metrics)
                        self.duration_plot = ui.plotly(duration_fig).classes("w-full")

                    with ui.column().classes("flex-1"):
                        token_fig = create_token_chart(metrics)
                        self.token_plot = ui.plotly(token_fig).classes("w-full")

                # Throughput chart (full width)
                throughput_fig = create_tokens_per_second_chart(metrics)
                self.throughput_plot = ui.plotly(throughput_fig).classes("w-full")
                logger.info("Charts created successfully")
        else:
            logger.warning("Container is None, cannot refresh")


def create_performance_charts(
    repository: TaskRepository, task_id: int | None = None
) -> PerformanceCharts:
    """Create a performance charts component.

    Args:
        repository: Task repository for data access
        task_id: Optional task ID to filter metrics

    Returns:
        PerformanceCharts instance

    Example:
        >>> from src.database.connection import DatabaseConnection
        >>> from src.database.repositories import TaskRepository
        >>> db = DatabaseConnection("test.duckdb")
        >>> repo = TaskRepository(db)
        >>> charts = create_performance_charts(repo, task_id=1)
        >>> charts.create()
    """
    charts = PerformanceCharts(repository, task_id)
    charts.create()
    return charts
