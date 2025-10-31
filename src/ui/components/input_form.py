"""Task input form component.

This module provides a UI component for task prompt input.
"""

from collections.abc import Callable

from nicegui import ui


def create_task_input_form(on_submit: Callable[[str], None]) -> None:
    """Create a task input form with textarea and submit button.

    Args:
        on_submit: Callback function to execute when form is submitted.
                   Receives the prompt text as argument.

    Example:
        >>> def handle_submit(prompt: str):
        ...     print(f"Submitted: {prompt}")
        >>> create_task_input_form(handle_submit)
    """
    with ui.card().classes("w-full"):
        ui.label("Task Prompt").classes("text-h6")

        # Multi-line textarea for prompt input
        prompt_input = ui.textarea(
            label="Enter your task description",
            placeholder="Example: Check if 17 is a prime number",
        ).classes("w-full").props("rows=5")

        # Submit button
        def handle_click() -> None:
            """Handle submit button click."""
            prompt = prompt_input.value.strip() if prompt_input.value else ""
            if prompt:
                on_submit(prompt)
                prompt_input.value = ""  # Clear input after submission
            else:
                ui.notify("Please enter a task prompt", type="warning")

        ui.button("Execute Task", on_click=handle_click).props("color=primary")
