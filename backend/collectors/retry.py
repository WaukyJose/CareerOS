import logging
from time import sleep


logger = logging.getLogger("collectors.retry")


def retry_with_backoff(
    operation,
    *,
    attempts=3,
    initial_delay=0.5,
    backoff_factor=2,
    exceptions=(Exception,),
    sleeper=sleep,
):
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    if initial_delay < 0:
        raise ValueError("initial_delay must be non-negative")
    if backoff_factor < 1:
        raise ValueError("backoff_factor must be at least 1")

    delay = initial_delay
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except exceptions:
            if attempt == attempts:
                logger.exception("Operation failed after %s attempts.", attempts)
                raise
            logger.warning(
                "Operation failed on attempt %s/%s. Retrying in %s seconds.",
                attempt,
                attempts,
                delay,
                exc_info=True,
            )
            sleeper(delay)
            delay *= backoff_factor

    raise RuntimeError("retry_with_backoff reached an unreachable state")
