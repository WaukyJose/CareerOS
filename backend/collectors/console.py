import logging
from contextlib import contextmanager


@contextmanager
def collector_console_logging(*, verbose=False):
    """Keep collector logs quiet for concise commands unless explicitly requested."""
    collector_logger = logging.getLogger("collectors")
    previous_level = collector_logger.level
    if not verbose:
        collector_logger.setLevel(logging.CRITICAL + 1)
    try:
        yield
    finally:
        collector_logger.setLevel(previous_level)
