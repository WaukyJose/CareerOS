import re
from io import StringIO

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import models

from collectors.console import collector_console_logging
from collectors.models import CollectorExecution


MATCH_SUMMARY = re.compile(r"Matches computed: created=(\d+) updated=(\d+)")


class Command(BaseCommand):
    help = "Run all collectors, then recompute job matches."

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show retry diagnostics and full collector tracebacks.",
        )

    def handle(self, *args, **options):
        with collector_console_logging(verbose=options["verbose"]):
            return self._handle(*args, **options)

    def _handle(self, *args, **options):
        last_execution_id = (
            CollectorExecution.objects.order_by("-id")
            .values_list("id", flat=True)
            .first()
            or 0
        )
        collector_output = StringIO()
        match_output = StringIO()

        try:
            call_command(
                "run_collectors",
                stdout=collector_output,
                stderr=StringIO(),
                verbose=options["verbose"],
            )
            executions = CollectorExecution.objects.filter(id__gt=last_execution_id)
            collector_totals = executions.aggregate(
                new=models.Sum("new"),
                updated=models.Sum("updated"),
                skipped=models.Sum("skipped"),
                errors=models.Sum("errors"),
            )

            call_command("compute_matches", stdout=match_output)
            match = MATCH_SUMMARY.search(match_output.getvalue())
            if match is None:
                raise RuntimeError("compute_matches did not return its expected summary")
        except Exception as exc:
            if isinstance(exc, CommandError):
                raise
            raise CommandError(f"Job refresh failed: {exc}") from exc

        collector_lines = [
            line
            for line in collector_output.getvalue().splitlines()
            if line and line != "No collectors registered."
        ]
        for line in collector_lines:
            self.stdout.write(line)
        self.stdout.write("Collectors summary:")
        for field in ("new", "updated", "skipped", "errors"):
            self.stdout.write(f"- {field}: {collector_totals[field] or 0}")
        self.stdout.write("Matches:")
        self.stdout.write(f"- created: {match.group(1)}")
        self.stdout.write(f"- updated: {match.group(2)}")
