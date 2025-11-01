"""Task input form component.

This module provides a UI component for task prompt input.
"""

import logging
from collections.abc import Awaitable, Callable

from nicegui import ui

logger = logging.getLogger(__name__)


def create_task_input_form(on_submit: Callable[[str], None | Awaitable[None]]) -> None:
    """Create a task input form with textarea and submit button.

    Args:
        on_submit: Callback function to execute when form is submitted.
                   Can be either a synchronous or asynchronous function.
                   Receives the prompt text as argument.

    Example:
        >>> def handle_submit(prompt: str):
        ...     print(f"Submitted: {prompt}")
        >>> create_task_input_form(handle_submit)

        >>> async def async_handle_submit(prompt: str):
        ...     await process_prompt(prompt)
        >>> create_task_input_form(async_handle_submit)
    """
    with ui.card().classes("w-full"):
        ui.label("Task Prompt").classes("text-h6")

        # Multi-line textarea for prompt input
        prompt_input = (
            ui.textarea(
                label="Enter your task description",
                placeholder="Example: Check if 17 is a prime number",
            )
            .classes("w-full")
            .props("rows=5")
        )

        # Submit button
        async def handle_click() -> None:
            """Handle submit button click."""
            logger.info("Submit button clicked")
            prompt = prompt_input.value.strip() if prompt_input.value else ""
            logger.info(f"Prompt value: {prompt[:50] if prompt else '(empty)'}...")

            if prompt:
                logger.info("Calling on_submit callback")
                try:
                    result = on_submit(prompt)
                    # Handle both sync and async callbacks
                    if isinstance(result, Awaitable):
                        logger.info("Awaiting async callback")
                        await result
                    logger.info("Callback completed, clearing input")
                    prompt_input.value = ""  # Clear input after submission
                except Exception as e:
                    logger.error(f"Error in submit callback: {e}", exc_info=True)
                    ui.notify(f"Error: {str(e)}", type="negative")
            else:
                logger.warning("Empty prompt, showing warning")
                ui.notify("Please enter a task prompt", type="warning")

        ui.button("Execute Task", on_click=handle_click).props("color=primary")
