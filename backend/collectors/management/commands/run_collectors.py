from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

from collectors.models import Collector, CollectorExecution
from collectors.registry import registry
from jobs.services import JobService


class Command(BaseCommand):
    help = "Run registered collectors."

    def add_arguments(self, parser):
        parser.add_argument(
            "collector_names",
            nargs="*",
            help="Optional collector names. Runs all registered collectors when omitted.",
        )

    def handle(self, *args, **options):
        requested_names = options["collector_names"]
        selected = registry.enabled_definitions(requested_names)

        if requested_names:
            selected_names = {collector.name for collector in selected}
            missing = [name for name in requested_names if name not in selected_names]
            if missing:
                raise CommandError(f"Unknown enabled collector(s): {', '.join(missing)}")

        if not selected:
            self.stdout.write("No collectors registered.")
            return

        for collector_definition in selected:
            started_at = timezone.now()
            result = None
            collector_definition.last_run = started_at
            collector_definition.status = Collector.Status.RUNNING
            collector_definition.save(update_fields=["last_run", "status", "updated_at"])
            try:
                collector_class = registry.load_class(collector_definition.module_path)
                collector = collector_class(collector_config=collector_definition)
                result = self._run_and_persist(collector)
            except (ImproperlyConfigured, TypeError) as exc:
                result = self._error_result(str(exc))
            finished_at = timezone.now()
            CollectorExecution.objects.create(
                collector_name=collector_definition.name,
                started_at=started_at,
                finished_at=finished_at,
                new=result.new,
                updated=result.updated,
                skipped=result.skipped,
                errors=len(result.errors),
            )
            update_fields = ["status", "updated_at"]
            if result.succeeded:
                collector_definition.status = Collector.Status.SUCCESS
                collector_definition.last_success = finished_at
                update_fields.append("last_success")
            else:
                collector_definition.status = Collector.Status.ERROR
            collector_definition.save(update_fields=update_fields)
            self.stdout.write(
                f"{collector_definition.name}: new={result.new} updated={result.updated} "
                f"skipped={result.skipped} errors={len(result.errors)}"
            )

    def _error_result(self, message):
        from collectors.types import CollectorResult

        result = CollectorResult()
        result.add_error(message)
        return result

    def _run_and_persist(self, collector):
        result = collector.result_class()
        collector.logger.info("Starting collector: %s", collector.name)
        try:
            records = list(collector.collect())
        except Exception as exc:
            collector.logger.exception("Collector failed: %s", collector.name)
            result.add_error(str(exc))
            return result

        for record in records:
            try:
                upsert_result = JobService.upsert(record)
            except Exception as exc:
                collector.logger.exception("Failed to persist job record: %s", record.source_id)
                result.add_error(str(exc))
                continue
            if upsert_result.created:
                result.new += 1
            elif upsert_result.updated:
                result.updated += 1
            else:
                result.skipped += 1

        collector.logger.info(
            "Finished collector: %s new=%s updated=%s skipped=%s errors=%s",
            collector.name,
            result.new,
            result.updated,
            result.skipped,
            len(result.errors),
        )
        return result
