"""Shared utility functions for CleanBox application."""
import functools
import logging
import time
from typing import TypeVar, Callable, Any, Type, Tuple, Optional

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Retry decorator for flaky operations.

    Args:
        max_attempts: Maximum number of retry attempts.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for delay after each retry.
        exceptions: Tuple of exceptions to catch and retry on.
        on_retry: Optional callback called on each retry with (exception, attempt).

    Returns:
        Decorated function that will retry on failure.

    Example:
        @retry(max_attempts=3, delay=1.0, exceptions=(IOError,))
        def read_file(path):
            return open(path).read()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        """Inner decorator that wraps the function."""
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            """Wrapper that implements retry logic."""
            current_delay = delay
            last_exception: Optional[Exception] = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {current_delay:.1f}s..."
                    )

                    if on_retry:
                        on_retry(e, attempt)

                    time.sleep(current_delay)
                    current_delay *= backoff

            # Should never reach here, but satisfy type checker
            raise last_exception  # type: ignore

        return wrapper
    return decorator


def safe_execute(
    func: Callable[..., T],
    *args: Any,
    default: T = None,  # type: ignore
    log_error: bool = True,
    **kwargs: Any,
) -> T:
    """
    Safely execute a function, returning default on error.

    Args:
        func: Function to execute.
        *args: Positional arguments to pass to function.
        default: Default value to return on error.
        log_error: Whether to log the error.
        **kwargs: Keyword arguments to pass to function.

    Returns:
        Function result or default value on error.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_error:
            logger.error(f"{func.__name__} failed: {e}")
        return default
