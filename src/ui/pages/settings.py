"""Settings page.

This module provides the settings page for configuring AI models
and application settings with persistence to config.toml.
"""

from pathlib import Path

from nicegui import ui

from src.config.loader import ConfigLoader
from src.config.models import AppConfig
from src.database.connection import DatabaseConnection
from src.ui.components.settings import SettingsForm, create_settings_form


class SettingsPage:
    """Settings page controller.

    Handles configuration form display, validation, and persistence.
    """

    def __init__(self, config: AppConfig, config_path: str | Path, db: DatabaseConnection):
        """Initialize settings page.

        Args:
            config: Current application configuration
            config_path: Path to config.toml file
            db: Database connection (for validation)
        """
        self.config = config
        self.config_path = Path(config_path)
        self.db = db
        self.form: SettingsForm | None = None
        self.status_label: ui.label | None = None

    def create(self) -> None:
        """Create the settings page UI."""
        ui.label("Settings").classes("text-h4 text-center")
        ui.label("Configure AI models and application settings").classes(
            "text-subtitle2 text-center text-grey-7 mb-4"
        )

        # Create settings form
        self.form = create_settings_form(self.config)

        # Action buttons
        with ui.row().classes("w-full justify-end gap-4 mt-6"):
            ui.button("Cancel", icon="cancel", on_click=self._on_cancel).props(
                "outline color=grey"
            )
            ui.button("Save Configuration", icon="save", on_click=self._on_save).props(
                "color=primary"
            )

        # Status message area
        with ui.row().classes("w-full justify-center mt-4"):
            self.status_label = ui.label("").classes("text-center")

    def _on_save(self) -> None:
        """Handle save button click."""
        if not self.form:
            self._show_error("Form not initialized")
            return

        try:
            # Get configuration from form
            new_config = self.form.get_config()

            # Validate configuration
            ConfigLoader.validate_dict(new_config.model_dump())

            # Save to TOML file
            ConfigLoader.save(new_config, self.config_path)

            # Update current config
            self.config = new_config

            self._show_success(
                f"Configuration saved successfully to {self.config_path.name}. "
                "Restart the application for changes to take effect."
            )

        except ValueError as e:
            self._show_error(f"Validation error: {e}")
        except Exception as e:
            self._show_error(f"Failed to save configuration: {e}")

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        # Reload form with original config
        if self.form and self.form.task_agents_container:
            # Clear existing forms
            for form in list(self.form.task_agent_forms):
                if form.container:
                    form.container.delete()
            self.form.task_agent_forms.clear()

            # Recreate form with original config
            self.form = create_settings_form(self.config)

        self._show_info("Changes discarded. Form reset to current configuration.")

    def _show_success(self, message: str) -> None:
        """Show success message.

        Args:
            message: Success message to display
        """
        if self.status_label:
            self.status_label.text = message
            self.status_label.classes("text-green-600", remove="text-red-600 text-blue-600")

        ui.notify(message, type="positive")

    def _show_error(self, message: str) -> None:
        """Show error message.

        Args:
            message: Error message to display
        """
        if self.status_label:
            self.status_label.text = message
            self.status_label.classes("text-red-600", remove="text-green-600 text-blue-600")

        ui.notify(message, type="negative")

    def _show_info(self, message: str) -> None:
        """Show info message.

        Args:
            message: Info message to display
        """
        if self.status_label:
            self.status_label.text = message
            self.status_label.classes("text-blue-600", remove="text-green-600 text-red-600")

        ui.notify(message, type="info")


def create_settings_page(
    config: AppConfig, config_path: str | Path, db: DatabaseConnection
) -> None:
    """Create the settings page.

    Args:
        config: Current application configuration
        config_path: Path to config.toml file
        db: Database connection

    Example:
        >>> from src.config.loader import ConfigLoader
        >>> from src.database.connection import DatabaseConnection
        >>> config = ConfigLoader.load("config.toml")
        >>> db = DatabaseConnection("data.duckdb")
        >>> create_settings_page(config, "config.toml", db)
    """
    page = SettingsPage(config, config_path, db)
    page.create()
