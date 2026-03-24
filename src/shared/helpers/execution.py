"""Generic execution helpers shared across modules."""
import functools
import logging
import time
from typing import Any, Callable, Optional, Tuple, Type, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Retry decorator for flaky operations."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception: Optional[Exception] = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as error:
                    last_exception = error
                    if attempt == max_attempts:
                        logger.error(
                            "%s failed after %s attempts: %s",
                            func.__name__,
                            max_attempts,
                            error,
                        )
                        raise

                    logger.warning(
                        "%s attempt %s/%s failed: %s. Retrying in %.1fs...",
                        func.__name__,
                        attempt,
                        max_attempts,
                        error,
                        current_delay,
                    )

                    if on_retry:
                        on_retry(error, attempt)

                    time.sleep(current_delay)
                    current_delay *= backoff

            raise last_exception  # type: ignore[misc]

        return wrapper

    return decorator


def safe_execute(
    func: Callable[..., T],
    *args: Any,
    default: T = None,  # type: ignore[assignment]
    log_error: bool = True,
    **kwargs: Any,
) -> T:
    """Safely execute a function, returning a default on error."""
    try:
        return func(*args, **kwargs)
    except Exception as error:
        if log_error:
            logger.error("%s failed: %s", func.__name__, error)
        return default
