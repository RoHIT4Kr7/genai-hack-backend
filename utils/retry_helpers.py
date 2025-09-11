"""
Exponential backoff retry utilities for Google API rate limiting.
"""

import asyncio
import random
import time
from typing import Callable, Any, Optional, Union
from loguru import logger
from functools import wraps


class RetryableError(Exception):
    """Base exception for retryable errors."""

    pass


class RateLimitError(RetryableError):
    """Exception for rate limit errors."""

    pass


async def exponential_backoff_async(
    func: Callable,
    *args,
    max_retries: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple = None,
    **kwargs,
) -> Any:
    """
    Execute an async function with exponential backoff retry logic.

    Args:
        func: The async function to execute
        *args: Arguments to pass to the function
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff calculation
        jitter: Whether to add random jitter to delay
        retryable_exceptions: Tuple of exception types that should trigger retry
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The result of the successful function call

    Raises:
        The last exception if all retries are exhausted
    """
    if retryable_exceptions is None:
        # Default retryable exceptions for Google APIs
        retryable_exceptions = (Exception,)  # Catch all for now, can be more specific

    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            # Try to execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = await asyncio.to_thread(func, *args, **kwargs)

            if attempt > 0:
                logger.info(f"Function succeeded on retry attempt {attempt}")

            return result

        except Exception as e:
            last_exception = e

            # Check if this is a retryable error
            is_retryable = any(
                isinstance(e, exc_type) for exc_type in retryable_exceptions
            )

            # Check for specific rate limit indicators
            error_str = str(e).lower()
            is_rate_limit = any(
                keyword in error_str
                for keyword in [
                    "rate limit",
                    "quota",
                    "too many requests",
                    "429",
                    "throttled",
                    "resource_exhausted",
                    "quota_exceeded",
                    "rate_limited",
                ]
            )

            # Special handling for quota exceeded errors
            is_quota_exceeded = "quota exceeded" in error_str.lower()

            if not is_retryable and not is_rate_limit:
                logger.warning(f"Non-retryable error encountered: {e}")
                raise e

            if attempt >= max_retries:
                logger.error(
                    f"All {max_retries} retry attempts exhausted for function {func.__name__}"
                )
                raise e

            # Calculate delay with exponential backoff
            # For quota exceeded errors, use optimized delays
            if is_quota_exceeded:
                # Use shorter, more aggressive delays for quota issues to recover faster
                base_delay = min(
                    initial_delay * (1.5**attempt),  # Slower exponential growth
                    30.0,  # Cap at 30 seconds instead of 60
                )
            else:
                base_delay = min(initial_delay * (exponential_base**attempt), max_delay)

            # Add jitter to prevent thundering herd
            if jitter:
                delay = base_delay * (
                    0.5 + random.random() * 0.5
                )  # Random factor between 0.5 and 1.0
            else:
                delay = base_delay

            logger.warning(
                f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                f"Retrying in {delay:.2f} seconds... "
                f"{'[QUOTA EXCEEDED - EXTENDED DELAY]' if is_quota_exceeded else ''}"
            )

            await asyncio.sleep(delay)

    # This should never be reached, but just in case
    if last_exception:
        raise last_exception
    else:
        raise Exception("Unknown error in exponential backoff")


def exponential_backoff_sync(
    func: Callable,
    *args,
    max_retries: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple = None,
    **kwargs,
) -> Any:
    """
    Execute a synchronous function with exponential backoff retry logic.

    Args:
        func: The synchronous function to execute
        *args: Arguments to pass to the function
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff calculation
        jitter: Whether to add random jitter to delay
        retryable_exceptions: Tuple of exception types that should trigger retry
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The result of the successful function call

    Raises:
        The last exception if all retries are exhausted
    """
    if retryable_exceptions is None:
        # Default retryable exceptions for Google APIs
        retryable_exceptions = (Exception,)  # Catch all for now, can be more specific

    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            # Try to execute the function
            result = func(*args, **kwargs)

            if attempt > 0:
                logger.info(f"Function succeeded on retry attempt {attempt}")

            return result

        except Exception as e:
            last_exception = e

            # Check if this is a retryable error
            is_retryable = any(
                isinstance(e, exc_type) for exc_type in retryable_exceptions
            )

            # Check for specific rate limit indicators
            error_str = str(e).lower()
            is_rate_limit = any(
                keyword in error_str
                for keyword in [
                    "rate limit",
                    "quota",
                    "too many requests",
                    "429",
                    "throttled",
                    "resource_exhausted",
                    "quota_exceeded",
                    "rate_limited",
                ]
            )

            if not is_retryable and not is_rate_limit:
                logger.warning(f"Non-retryable error encountered: {e}")
                raise e

            if attempt >= max_retries:
                logger.error(
                    f"All {max_retries} retry attempts exhausted for function {func.__name__}"
                )
                raise e

            # Calculate delay with exponential backoff
            delay = min(initial_delay * (exponential_base**attempt), max_delay)

            # Add jitter to prevent thundering herd
            if jitter:
                delay *= (
                    0.5 + random.random() * 0.5
                )  # Random factor between 0.5 and 1.0

            logger.warning(
                f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                f"Retrying in {delay:.2f} seconds..."
            )

            time.sleep(delay)

    # This should never be reached, but just in case
    if last_exception:
        raise last_exception
    else:
        raise Exception("Unknown error in exponential backoff")


def retry_with_backoff(
    max_retries: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple = None,
):
    """
    Decorator for adding exponential backoff retry logic to functions.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff calculation
        jitter: Whether to add random jitter to delay
        retryable_exceptions: Tuple of exception types that should trigger retry
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await exponential_backoff_async(
                func,
                *args,
                max_retries=max_retries,
                initial_delay=initial_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                jitter=jitter,
                retryable_exceptions=retryable_exceptions,
                **kwargs,
            )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return exponential_backoff_sync(
                func,
                *args,
                max_retries=max_retries,
                initial_delay=initial_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                jitter=jitter,
                retryable_exceptions=retryable_exceptions,
                **kwargs,
            )

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
