"""Settings form component.

This module provides UI components for configuring AI models and application settings.
"""

from collections.abc import Callable

from nicegui import ui

from src.config.models import AppConfig, EvaluationConfig, ModelConfig


class ModelConfigForm:
    """Form for configuring a single AI model.

    Provides inputs for provider, model name, and API key environment variable.
    """

    def __init__(
        self,
        model_config: ModelConfig | None = None,
        on_remove: Callable[[], None] | None = None,
    ):
        """Initialize model config form.

        Args:
            model_config: Optional existing model configuration to edit
            on_remove: Optional callback when remove button is clicked
        """
        self.model_config = model_config
        self.on_remove = on_remove
        self.provider_select: ui.select | None = None
        self.model_input: ui.input | None = None
        self.api_key_env_input: ui.input | None = None
        self.container: ui.card | None = None

    def create(self) -> None:
        """Create the model config form UI."""
        with ui.card().classes("w-full p-4") as card:
            self.container = card

            with ui.row().classes("w-full items-center gap-4"):
                # Provider selection
                self.provider_select = ui.select(
                    options=["openai", "anthropic", "gemini"],
                    label="Provider",
                    value=self.model_config.provider if self.model_config else "openai",
                ).classes("w-1/4")

                # Model name
                self.model_input = ui.input(
                    label="Model Name",
                    placeholder="e.g., gpt-4o, claude-sonnet-4",
                    value=self.model_config.model if self.model_config else "",
                ).classes("w-1/3")

                # API key env var
                self.api_key_env_input = ui.input(
                    label="API Key Env Var",
                    placeholder="e.g., OPENAI_API_KEY",
                    value=self.model_config.api_key_env if self.model_config else "",
                ).classes("w-1/3")

                # Remove button (if callback provided)
                if self.on_remove:
                    ui.button(icon="delete", on_click=self.on_remove).props("flat color=red")

    def get_config(self) -> ModelConfig:
        """Get the model configuration from form inputs.

        Returns:
            ModelConfig with values from form

        Raises:
            ValueError: If any required field is empty
        """
        if not self.provider_select or not self.model_input or not self.api_key_env_input:
            raise ValueError("Form not initialized")

        provider = self.provider_select.value
        model = self.model_input.value
        api_key_env = self.api_key_env_input.value

        if not provider or not model or not api_key_env:
            raise ValueError("All fields are required")

        return ModelConfig(provider=provider, model=str(model), api_key_env=str(api_key_env))


class SettingsForm:
    """Complete settings form for application configuration.

    Manages task agents, evaluation agent, execution settings, and database config.
    """

    def __init__(self, config: AppConfig):
        """Initialize settings form.

        Args:
            config: Current application configuration
        """
        self.config = config
        self.task_agent_forms: list[ModelConfigForm] = []
        self.eval_agent_form: ModelConfigForm | None = None
        self.timeout_input: ui.number | None = None
        self.db_path_input: ui.input | None = None
        self.eval_prompt_input: ui.textarea | None = None
        self.task_agents_container: ui.column | None = None

    def create(self) -> None:
        """Create the complete settings form UI."""
        ui.label("Application Settings").classes("text-h5")

        # Task Agents Section
        ui.label("Task Agents (2-5 required)").classes("text-h6 mt-4")
        ui.label("Configure the AI models that will execute tasks").classes(
            "text-caption text-grey-7"
        )

        with ui.column().classes("w-full gap-2") as agents_container:
            self.task_agents_container = agents_container

            # Create forms for existing task agents
            for agent_config in self.config.task_agents:
                self._add_task_agent_form(agent_config)

        # Add agent button
        ui.button("Add Task Agent", icon="add", on_click=self._add_task_agent_form).props(
            "outline color=primary"
        ).bind_enabled_from(self, "task_agent_forms", backward=lambda forms: len(forms) < 5)

        # Evaluation Agent Section
        ui.label("Evaluation Agent").classes("text-h6 mt-6")
        ui.label("Configure the AI model that will evaluate task results").classes(
            "text-caption text-grey-7"
        )

        self.eval_agent_form = ModelConfigForm(
            ModelConfig(
                provider=self.config.evaluation_agent.provider,
                model=self.config.evaluation_agent.model,
                api_key_env=self.config.evaluation_agent.api_key_env,
            )
        )
        self.eval_agent_form.create()

        # Evaluation prompt
        self.eval_prompt_input = (
            ui.textarea(
                label="Evaluation Prompt Template",
                value=self.config.evaluation_agent.prompt,
                placeholder="Use {task_prompt} and {agent_response} placeholders",
            )
            .classes("w-full")
            .props("rows=5")
        )

        # Execution Settings Section
        ui.label("Execution Settings").classes("text-h6 mt-6")

        with ui.row().classes("w-full gap-4"):
            self.timeout_input = ui.number(
                label="Timeout (seconds)",
                value=self.config.execution.timeout_seconds,
                min=1,
                max=600,
                step=1,
            ).classes("w-1/3")

            self.db_path_input = ui.input(
                label="Database Path",
                value=self.config.database.path,
                placeholder="e.g., agent_leaderboard.duckdb",
            ).classes("w-2/3")

    def _add_task_agent_form(self, model_config: ModelConfig | None = None) -> None:
        """Add a task agent form to the list.

        Args:
            model_config: Optional existing config to populate form
        """
        if not self.task_agents_container:
            raise RuntimeError("Task agents container not initialized")

        def remove_form() -> None:
            # Find and remove this form
            if form in self.task_agent_forms:
                self.task_agent_forms.remove(form)
                if form.container:
                    form.container.delete()

        with self.task_agents_container:
            on_remove_callback = remove_form if len(self.task_agent_forms) >= 2 else None
            form = ModelConfigForm(model_config, on_remove=on_remove_callback)
            form.create()
            self.task_agent_forms.append(form)

    def get_config(self) -> AppConfig:
        """Get the application configuration from form inputs.

        Returns:
            AppConfig with values from form

        Raises:
            ValueError: If validation fails
        """
        # Validate task agents count
        if len(self.task_agent_forms) < 2:
            raise ValueError("At least 2 task agents are required")
        if len(self.task_agent_forms) > 5:
            raise ValueError("Maximum 5 task agents allowed")

        # Collect task agents
        task_agents = []
        for form in self.task_agent_forms:
            task_agents.append(form.get_config())

        # Get evaluation agent
        if not self.eval_agent_form:
            raise ValueError("Evaluation agent not configured")

        eval_model = self.eval_agent_form.get_config()

        if not self.eval_prompt_input or not self.eval_prompt_input.value:
            raise ValueError("Evaluation prompt is required")

        evaluation_agent = EvaluationConfig(
            provider=eval_model.provider,
            model=eval_model.model,
            api_key_env=eval_model.api_key_env,
            prompt=str(self.eval_prompt_input.value),
        )

        # Get execution settings
        if not self.timeout_input or not self.timeout_input.value:
            raise ValueError("Timeout is required")

        # Get database path
        if not self.db_path_input or not self.db_path_input.value:
            raise ValueError("Database path is required")

        # Create AppConfig
        from src.config.models import DatabaseConfig, ExecutionConfig

        return AppConfig(
            execution=ExecutionConfig(timeout_seconds=int(self.timeout_input.value)),
            task_agents=task_agents,
            evaluation_agent=evaluation_agent,
            database=DatabaseConfig(path=str(self.db_path_input.value)),
        )


def create_settings_form(config: AppConfig) -> SettingsForm:
    """Create a settings form component.

    Args:
        config: Current application configuration

    Returns:
        SettingsForm instance

    Example:
        >>> from src.config.loader import ConfigLoader
        >>> config = ConfigLoader.load("config.toml")
        >>> form = create_settings_form(config)
        >>> form.create()
    """
    form = SettingsForm(config)
    form.create()
    return form
