import logging
import socket
from time import sleep
from urllib.error import HTTPError, URLError


logger = logging.getLogger("collectors.retry")

TRANSIENT_HTTP_STATUSES = {408, 425, 429, 500, 502, 503, 504}


def is_transient_network_error(exc):
    if isinstance(exc, HTTPError):
        return exc.code in TRANSIENT_HTTP_STATUSES
    if isinstance(exc, (TimeoutError, socket.timeout, ConnectionError)):
        return True
    if isinstance(exc, URLError):
        return True
    return False


def error_reason(exc):
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return f"Timeout: {exc}"
    if isinstance(exc, URLError) and isinstance(exc.reason, (TimeoutError, socket.timeout)):
        return f"Timeout: {exc.reason}"
    return f"{type(exc).__name__}: {exc}"


def retry_with_backoff(
    operation,
    *,
    attempts=3,
    initial_delay=0.5,
    backoff_factor=2,
    exceptions=None,
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
        except Exception as exc:
            should_retry = (
                isinstance(exc, exceptions)
                if exceptions is not None
                else is_transient_network_error(exc)
            )
            if not should_retry:
                raise
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
