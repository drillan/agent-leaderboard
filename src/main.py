"""Main application entry point.

This module initializes and runs the Multi-Agent Competition System.
"""

import argparse
import sys
from pathlib import Path

from nicegui import ui

from src.config.loader import ConfigLoader
from src.database.connection import DatabaseConnection
from src.ui.pages.main import create_main_page
from src.ui.pages.performance import create_performance_page


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Multi-Agent Competition System - Execute tasks across multiple AI models"
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config.toml",
        help="Path to configuration file (default: config.toml)",
    )

    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help="Path to DuckDB database file (default: from config.toml)",
    )

    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the web server (default: 0.0.0.0)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to bind the web server (default: 8080)",
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes (development mode)",
    )

    return parser.parse_args()


def main() -> None:
    """Main application entry point."""
    args = parse_args()

    # Load configuration
    try:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"Error: Configuration file not found: {args.config}", file=sys.stderr)
            sys.exit(1)

        config = ConfigLoader.load(config_path)
        print(f"✓ Configuration loaded from {args.config}")

    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # Initialize database
    try:
        db_path = args.db if args.db else config.database.path
        db = DatabaseConnection(db_path)
        db.initialize_schema()
        print(f"✓ Database initialized at {db_path}")

    except Exception as e:
        print(f"Error initializing database: {e}", file=sys.stderr)
        sys.exit(1)

    # Create UI
    @ui.page("/")
    def index() -> None:
        """Main page route with tab navigation."""
        # Create tabs
        with ui.tabs().classes("w-full") as tabs:
            main_tab = ui.tab("Task Execution", icon="play_arrow")
            perf_tab = ui.tab("Performance", icon="bar_chart")

        # Create tab panels
        with ui.tab_panels(tabs, value=main_tab).classes("w-full"):
            with ui.tab_panel(main_tab):
                create_main_page(config, db)

            with ui.tab_panel(perf_tab):
                create_performance_page(config, db)

    # Run application
    print("\n🚀 Starting Multi-Agent Competition System")
    print(f"   URL: http://{args.host}:{args.port}")
    print(f"   Agents configured: {len(config.task_agents)}")
    print(f"   Timeout: {config.execution.timeout_seconds}s")
    print("\nPress Ctrl+C to stop\n")

    ui.run(
        host=args.host,
        port=args.port,
        title="Multi-Agent Competition System",
        reload=args.reload,
        show=False,  # Don't auto-open browser
    )


if __name__ == "__main__":
    main()
