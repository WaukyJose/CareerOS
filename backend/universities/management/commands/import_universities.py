import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from universities.models import University


class Command(BaseCommand):
    help = "Import Ecuadorian universities from a CSV file."

    required_columns = {"name", "city", "province", "type", "website"}
    optional_columns = {"jobs_url"}

    def add_arguments(self, parser):
        default_path = Path(__file__).resolve().parents[4] / "data" / "ecuador_universities.csv"
        parser.add_argument(
            "csv_path",
            nargs="?",
            default=str(default_path),
            help="Path to a CSV file with name, city, province, type, and website columns.",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"])
        if not csv_path.exists():
            raise CommandError(f"CSV file not found: {csv_path}")

        created = 0
        updated = 0

        with csv_path.open(newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            missing_columns = self.required_columns - set(reader.fieldnames or [])
            if missing_columns:
                columns = ", ".join(sorted(missing_columns))
                raise CommandError(f"CSV file is missing required columns: {columns}")
            has_jobs_url_column = "jobs_url" in (reader.fieldnames or [])

            for row_number, row in enumerate(reader, start=2):
                data = self._clean_row(row, row_number)
                defaults = {
                    "city": data["city"],
                    "province": data["province"],
                    "type": data["type"],
                    "website": data["website"],
                    "status": University.RegistryStatus.ACTIVE,
                }
                if has_jobs_url_column:
                    defaults["jobs_url"] = data.get("jobs_url", "")

                _, was_created = University.objects.update_or_create(
                    name=data["name"],
                    defaults=defaults,
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported universities: {created} created, {updated} updated."
            )
        )

    def _clean_row(self, row, row_number):
        data = {
            column: (row.get(column) or "").strip()
            for column in self.required_columns | self.optional_columns
        }
        missing_values = [column for column in self.required_columns if not data[column]]
        if missing_values:
            columns = ", ".join(sorted(missing_values))
            raise CommandError(f"Row {row_number} is missing values for: {columns}")

        valid_types = {choice.value for choice in University.UniversityType}
        if data["type"] not in valid_types:
            allowed = ", ".join(sorted(valid_types))
            raise CommandError(
                f"Row {row_number} has invalid type '{data['type']}'. Allowed: {allowed}"
            )

        return data
