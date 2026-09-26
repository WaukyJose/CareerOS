import logging

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from collectors.generic_html import GenericHTMLCollector
from collectors.models import Collector, CollectorExecution
from collectors.registry import registry
from collectors.retry import error_reason


logger = logging.getLogger("collectors.test")


class Command(BaseCommand):
    help = "Fetch and preview jobs from one configured collector without persisting them."

    def add_arguments(self, parser):
        parser.add_argument("collector_name")

    def handle(self, *args, **options):
        name = options["collector_name"]
        try:
            definition = Collector.objects.select_related("university", "template").get(name=name)
        except Collector.DoesNotExist as exc:
            raise CommandError(f"Collector not found: {name}") from exc

        started_at = timezone.now()
        definition.last_run = started_at
        definition.save(update_fields=["last_run", "updated_at"])
        logger.info("Collector test started name=%s url=%s", name, definition.university.jobs_url)

        try:
            definition.full_clean()
            collector_class = registry.load_class(definition.module_path)
            collector = collector_class(collector_config=definition)
            records = list(collector.collect())
        except Exception as exc:
            reason = error_reason(exc)
            self._record_result(definition, started_at, 0, reason, failed=True)
            logger.exception("Collector test failed name=%s", name)
            raise CommandError(f"Collector test failed: {exc}") from exc

        for index, record in enumerate(records, start=1):
            self.stdout.write(f"{index}. {record.title} | {record.source_url}")
        self.stdout.write(self.style.SUCCESS(f"Extracted {len(records)} job(s)."))

        if isinstance(collector, GenericHTMLCollector):
            configured = [
                definition.config_value(field)
                for field in (
                    "list_selector", "title_selector", "link_selector",
                    "date_selector", "description_selector",
                )
                if definition.config_value(field)
            ]
            for selector in configured:
                if collector.selector_matches.get(selector, 0) == 0:
                    self.stderr.write(self.style.WARNING(f"Selector matched no elements: {selector}"))

        self._record_result(definition, started_at, len(records), "", failed=False)
        logger.info("Collector test finished name=%s jobs=%s", name, len(records))

    @staticmethod
    def _record_result(definition, started_at, job_count, error, *, failed):
        finished_at = timezone.now()
        CollectorExecution.objects.create(
            collector_name=definition.name,
            started_at=started_at,
            finished_at=finished_at,
            skipped=job_count,
            errors=1 if failed else 0,
            error_reason=error,
        )
        definition.last_job_count = job_count
        definition.last_duration = finished_at - started_at
        definition.last_error = error
        definition.health_status = (
            Collector.HealthStatus.ERROR
            if failed
            else Collector.HealthStatus.HEALTHY if job_count else Collector.HealthStatus.EMPTY
        )
        definition.save(update_fields=[
            "health_status", "last_job_count", "last_duration", "last_error", "updated_at",
        ])
