from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase

from .models import University


class UniversityModelTests(TestCase):
    def test_string_representation_uses_name(self):
        university = University.objects.create(
            name="Universidad de Prueba",
            city="Quito",
            province="Pichincha",
            type=University.UniversityType.PUBLIC,
            website="https://example.edu.ec",
        )

        self.assertEqual(str(university), "Universidad de Prueba")

    def test_default_status_is_active(self):
        university = University.objects.create(
            name="Universidad Activa",
            city="Cuenca",
            province="Azuay",
            type=University.UniversityType.PRIVATE_COFINANCED,
            website="https://active.example.edu.ec",
        )

        self.assertEqual(university.status, University.RegistryStatus.ACTIVE)


class ImportUniversitiesCommandTests(TestCase):
    def test_import_creates_universities_from_csv(self):
        csv_path = self._write_csv(
            "name,city,province,type,website\n"
            "Universidad Uno,Quito,Pichincha,public,https://uno.edu.ec\n"
            "Universidad Dos,Guayaquil,Guayas,private_selffinanced,https://dos.edu.ec\n"
        )

        stdout = StringIO()
        call_command("import_universities", str(csv_path), stdout=stdout)

        self.assertEqual(University.objects.count(), 2)
        self.assertIn("2 created, 0 updated", stdout.getvalue())

    def test_import_is_idempotent_and_updates_existing_records(self):
        first_csv = self._write_csv(
            "name,city,province,type,website\n"
            "Universidad Uno,Quito,Pichincha,public,https://old.example.edu.ec\n"
        )
        second_csv = self._write_csv(
            "name,city,province,type,website\n"
            "Universidad Uno,Sangolqui,Pichincha,public,https://new.example.edu.ec\n"
        )

        call_command("import_universities", str(first_csv), stdout=StringIO())
        call_command("import_universities", str(second_csv), stdout=StringIO())

        university = University.objects.get(name="Universidad Uno")
        self.assertEqual(University.objects.count(), 1)
        self.assertEqual(university.city, "Sangolqui")
        self.assertEqual(university.website, "https://new.example.edu.ec")

    def test_import_without_jobs_url_column_preserves_existing_jobs_url(self):
        University.objects.create(
            name="Universidad Uno",
            city="Quito",
            province="Pichincha",
            type=University.UniversityType.PUBLIC,
            website="https://old.example.edu.ec",
            jobs_url="https://jobs.example.edu.ec",
        )
        csv_path = self._write_csv(
            "name,city,province,type,website\n"
            "Universidad Uno,Sangolqui,Pichincha,public,https://new.example.edu.ec\n"
        )

        call_command("import_universities", str(csv_path), stdout=StringIO())

        university = University.objects.get(name="Universidad Uno")
        self.assertEqual(university.jobs_url, "https://jobs.example.edu.ec")

    def _write_csv(self, content):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        csv_path = Path(directory.name) / "universities.csv"
        csv_path.write_text(content, encoding="utf-8")
        return csv_path
