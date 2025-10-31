"""Main application entry point.

This module initializes and runs the Multi-Agent Competition System.
"""

import argparse
import logging
import sys
from pathlib import Path

from nicegui import ui

from src.config.loader import ConfigLoader
from src.database.connection import DatabaseConnection
from src.ui.pages.history import create_history_page
from src.ui.pages.main import create_main_page
from src.ui.pages.performance import create_performance_page
from src.ui.pages.settings import create_settings_page

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


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

    # Load and validate configuration
    try:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"\n❌ Error: Configuration file not found: {args.config}", file=sys.stderr)
            print(
                "   Please create a config.toml file or specify an existing file with --config",
                file=sys.stderr,
            )
            sys.exit(1)

        config = ConfigLoader.load(config_path)
        print(f"✓ Configuration loaded from {args.config}")

        # Validate configuration details
        print("✓ Configuration validation:")
        print(f"   - Task agents: {len(config.task_agents)} configured")
        for i, agent in enumerate(config.task_agents, 1):
            print(f"     {i}. {agent.provider}/{agent.model} (API key: {agent.api_key_env})")

        print(
            f"   - Evaluation agent: "
            f"{config.evaluation_agent.provider}/{config.evaluation_agent.model}"
        )
        print(f"   - Timeout: {config.execution.timeout_seconds}s")

    except ValueError as e:
        print("\n❌ Configuration validation error:", file=sys.stderr)
        print(f"   {e}", file=sys.stderr)
        print("\n   Common issues:", file=sys.stderr)
        print(
            f"   - Task agents: Must have 2-5 agents "
            f"(not {len(getattr(config, 'task_agents', []))} agents)",
            file=sys.stderr,
        )
        print(
            "   - Duplicate models: Each agent must use a unique provider/model combination",
            file=sys.stderr,
        )
        print(
            "   - API keys: All API key environment variables must be set and non-empty",
            file=sys.stderr,
        )
        print("   - Timeout: Must be between 1-600 seconds", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error loading configuration: {e}", file=sys.stderr)
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
            history_tab = ui.tab("History", icon="history")
            settings_tab = ui.tab("Settings", icon="settings")

        # Create tab panels
        with ui.tab_panels(tabs, value=main_tab).classes("w-full"):
            with ui.tab_panel(main_tab):
                create_main_page(config, db)

            with ui.tab_panel(perf_tab):
                create_performance_page(config, db)

            with ui.tab_panel(history_tab):
                create_history_page(config, db)

            with ui.tab_panel(settings_tab):
                create_settings_page(config, args.config, db)

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
