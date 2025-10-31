"""Timeout utilities for agent execution.

This module provides timeout wrapper functionality for async operations.
"""

import asyncio
from collections.abc import Coroutine
from typing import Any, TypeVar

T = TypeVar("T")


async def with_timeout(coro: Coroutine[Any, Any, T], timeout_seconds: float) -> T | None:
    """Execute an async coroutine with a timeout.

    Args:
        coro: The coroutine to execute
        timeout_seconds: Maximum execution time in seconds

    Returns:
        The result of the coroutine if completed within timeout, None otherwise

    Note:
        This function catches asyncio.TimeoutError and returns None instead
        of propagating the exception, making it easier to handle timeouts
        in the execution flow.
    """
    try:
        result = await asyncio.wait_for(coro, timeout=timeout_seconds)
        return result
    except TimeoutError:
        return None
