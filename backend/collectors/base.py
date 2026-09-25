import logging
from abc import ABC, abstractmethod

from .types import CollectorResult


class BaseCollector(ABC):
    """Base contract for source-specific opportunity collectors."""

    name = ""
    result_class = CollectorResult

    def __init__(self, logger=None, collector_config=None):
        if not self.name:
            raise ValueError("Collector classes must define a non-empty name.")
        self.logger = logger or logging.getLogger(f"collectors.{self.name}")
        self.collector_config = collector_config

    def run(self):
        self.logger.info("Starting collector: %s", self.name)
        result = CollectorResult()

        try:
            records = list(self.collect())
        except Exception as exc:
            self.logger.exception("Collector failed: %s", self.name)
            result.add_error(str(exc))
            return result

        for record in records:
            result.skipped += 1
            self.logger.debug("Collected job record without persistence: %s", record.source_id)

        self.logger.info(
            "Finished collector: %s new=%s updated=%s skipped=%s errors=%s",
            self.name,
            result.new,
            result.updated,
            result.skipped,
            len(result.errors),
        )
        return result

    @abstractmethod
    def collect(self):
        """Return an iterable of JobRecord instances."""
