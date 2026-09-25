from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase

from .base import BaseCollector
from .espe import ESPECollector
from .extraction import JobExtractor, LinkFilter
from .generic_html import GenericHTMLCollector
from .registry import CollectorRegistry, registry
from .retry import retry_with_backoff
from .types import JobRecord
from collectors.models import Collector, CollectorExecution
from jobs.models import Job
from universities.models import University


class ExampleCollector(BaseCollector):
    name = "example"

    def collect(self):
        return [
            JobRecord(
                source=self.name,
                source_id="job-1",
                title="Research Fellow",
                institution_name="Example University",
                source_url="https://example.edu/jobs/1",
            )
        ]


class FailingCollector(BaseCollector):
    name = "failing"

    def collect(self):
        raise RuntimeError("source unavailable")


class BaseCollectorTests(SimpleTestCase):
    def test_run_returns_collector_result_for_records(self):
        result = ExampleCollector().run()

        self.assertTrue(result.succeeded)
        self.assertEqual(result.new, 0)
        self.assertEqual(result.updated, 0)
        self.assertEqual(result.skipped, 1)
        self.assertEqual(result.errors, [])

    def test_run_records_errors_without_raising(self):
        result = FailingCollector().run()

        self.assertFalse(result.succeeded)
        self.assertEqual(result.errors, ["source unavailable"])

    def test_collector_requires_name(self):
        class NamelessCollector(BaseCollector):
            def collect(self):
                return []

        with self.assertRaisesMessage(ValueError, "non-empty name"):
            NamelessCollector()


class CollectorRegistryTests(SimpleTestCase):
    def test_register_and_get_collector(self):
        local_registry = CollectorRegistry()
        local_registry.register(ExampleCollector)

        self.assertIs(local_registry.get("example"), ExampleCollector)
        self.assertEqual(local_registry.all(), {"example": ExampleCollector})

    def test_duplicate_registration_is_rejected(self):
        local_registry = CollectorRegistry()
        local_registry.register(ExampleCollector)

        with self.assertRaisesMessage(ValueError, "already registered"):
            local_registry.register(ExampleCollector)

    def test_empty_name_registration_is_rejected(self):
        class EmptyNameCollector:
            name = ""

        with self.assertRaisesMessage(ValueError, "non-empty name"):
            CollectorRegistry().register(EmptyNameCollector)


class RetryWithBackoffTests(SimpleTestCase):
    def test_retries_until_operation_succeeds(self):
        calls = []
        sleeps = []

        def operation():
            calls.append("called")
            if len(calls) < 3:
                raise ValueError("temporary")
            return "ok"

        result = retry_with_backoff(
            operation,
            attempts=3,
            initial_delay=1,
            backoff_factor=2,
            exceptions=(ValueError,),
            sleeper=sleeps.append,
        )

        self.assertEqual(result, "ok")
        self.assertEqual(len(calls), 3)
        self.assertEqual(sleeps, [1, 2])

    def test_raises_after_final_attempt(self):
        sleeps = []

        def operation():
            raise ValueError("permanent")

        with self.assertRaisesMessage(ValueError, "permanent"):
            retry_with_backoff(
                operation,
                attempts=2,
                initial_delay=0.25,
                exceptions=(ValueError,),
                sleeper=sleeps.append,
            )

        self.assertEqual(sleeps, [0.25])

    def test_rejects_invalid_attempt_count(self):
        with self.assertRaisesMessage(ValueError, "attempts"):
            retry_with_backoff(lambda: None, attempts=0)


class RunCollectorsCommandTests(TestCase):
    def setUp(self):
        University.objects.create(
            name="Example University",
            city="Quito",
            province="Pichincha",
            type=University.UniversityType.PUBLIC,
            website="https://example.edu",
        )

    def test_command_reports_when_no_collectors_are_registered(self):
        stdout = StringIO()

        call_command("run_collectors", stdout=stdout)

        self.assertIn("No collectors registered.", stdout.getvalue())

    def test_command_runs_registered_collector(self):
        Collector.objects.create(
            university=University.objects.get(name="Example University"),
            name="example",
            module_path="collectors.tests.ExampleCollector",
        )
        stdout = StringIO()

        call_command("run_collectors", stdout=stdout)

        self.assertIn("example: new=1 updated=0 skipped=0 errors=0", stdout.getvalue())
        self.assertEqual(Job.objects.count(), 1)
        self.assertEqual(CollectorExecution.objects.count(), 1)
        collector = Collector.objects.get(name="example")
        self.assertEqual(collector.status, Collector.Status.SUCCESS)
        self.assertIsNotNone(collector.last_run)
        self.assertIsNotNone(collector.last_success)

    def test_command_rejects_unknown_requested_collector(self):
        with self.assertRaises(CommandError):
            call_command("run_collectors", "missing", stdout=StringIO())

    def test_disabled_collectors_are_skipped(self):
        Collector.objects.create(
            university=University.objects.get(name="Example University"),
            name="example",
            module_path="collectors.tests.ExampleCollector",
            enabled=False,
        )
        stdout = StringIO()

        call_command("run_collectors", stdout=stdout)

        self.assertIn("No collectors registered.", stdout.getvalue())
        self.assertEqual(Job.objects.count(), 0)

    def test_enabled_collectors_run_by_priority(self):
        university = University.objects.get(name="Example University")
        Collector.objects.create(
            university=university,
            name="second",
            module_path="collectors.tests.SecondExampleCollector",
            priority=20,
        )
        Collector.objects.create(
            university=university,
            name="first",
            module_path="collectors.tests.FirstExampleCollector",
            priority=10,
        )
        stdout = StringIO()

        call_command("run_collectors", stdout=stdout)

        lines = [line for line in stdout.getvalue().splitlines() if line]
        self.assertTrue(lines[0].startswith("first:"))
        self.assertTrue(lines[1].startswith("second:"))

    def test_invalid_module_path_records_error(self):
        Collector.objects.create(
            university=University.objects.get(name="Example University"),
            name="broken",
            module_path="collectors.tests.DoesNotExist",
        )
        stdout = StringIO()

        call_command("run_collectors", stdout=stdout)

        self.assertIn("broken: new=0 updated=0 skipped=0 errors=1", stdout.getvalue())
        collector = Collector.objects.get(name="broken")
        self.assertEqual(collector.status, Collector.Status.ERROR)
        self.assertEqual(CollectorExecution.objects.get().errors, 1)


class ESPECollectorTests(TestCase):
    def setUp(self):
        self.university = University.objects.create(
            name="Universidad de las Fuerzas Armadas ESPE",
            city="Ruminahui",
            province="Pichincha",
            type=University.UniversityType.PUBLIC,
            website="https://www.espe.edu.ec",
            jobs_url="https://uth.espe.edu.ec/concurso-de-meritos/",
        )
        self.sample_html = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "espe_jobs_sample.html"
        ).read_text(encoding="utf-8")

    def tearDown(self):
        pass

    def test_parse_fixture_html_returns_job_records(self):
        records = ESPECollector(fetcher=lambda url: self.sample_html).collect()

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].source, "espe")
        self.assertEqual(records[0].institution_name, self.university.name)
        self.assertEqual(records[0].location, "Ruminahui, Pichincha")
        self.assertEqual(
            records[0].source_url,
            "https://uth.espe.edu.ec/convocatorias/vacante-docente-tiempo-completo-sistemas/",
        )
        self.assertEqual(
            records[0].raw_data["source_page"],
            "https://uth.espe.edu.ec/concurso-de-meritos/",
        )
        self.assertTrue(all(not record.source_url.endswith(".pdf") for record in records))
        self.assertTrue(all("/download/" not in record.source_url for record in records))
        self.assertEqual(records[0].department, "Docencia")
        self.assertEqual(records[0].discipline, "Sistemas")
        self.assertEqual(records[0].employment_type, "Tiempo completo")
        self.assertEqual(records[0].posted_date.isoformat(), "2026-09-01")
        self.assertEqual(records[0].deadline_date.isoformat(), "2026-09-30")
        self.assertTrue(all("viewer" not in record.source_url for record in records))
        self.assertTrue(all("/empleos/" not in record.source_url for record in records))
        self.assertEqual(
            {record.source_url for record in records},
            {
                "https://uth.espe.edu.ec/convocatorias/vacante-docente-tiempo-completo-sistemas/",
                "https://uth.espe.edu.ec/convocatorias/convocatoria-docente-investigador-electronica/",
            },
        )

    def test_attachment_only_page_returns_zero_jobs(self):
        page = """
            <nav><a href='/jobs/'>Jobs</a></nav>
            <a href='/files/convocatoria.pdf'>Convocatoria docente</a>
            <a href='/download/vacante.zip'>Descargar vacante</a>
            <a href='/viewer?id=3'>Viewer convocatoria</a>
        """

        self.assertEqual(ESPECollector().parse(page, self.university), [])

    def test_missing_jobs_url_is_graceful(self):
        self.university.jobs_url = ""
        self.university.save(update_fields=["jobs_url"])

        records = ESPECollector(fetcher=lambda url: self.sample_html).collect()

        self.assertEqual(records, [])

    def test_run_records_fetch_errors_without_raising(self):
        def failing_fetcher(url):
            raise TimeoutError("timeout")

        result = ESPECollector(fetcher=failing_fetcher).run()

        self.assertFalse(result.succeeded)
        self.assertEqual(result.errors, ["timeout"])

    def test_run_collectors_executes_registered_espe_collector(self):
        Collector.objects.create(
            university=self.university,
            name="espe",
            module_path="collectors.espe.ESPECollector",
        )
        stdout = StringIO()

        with patch("collectors.espe.urlopen", return_value=FakeResponse(self.sample_html)):
            call_command("run_collectors", "espe", stdout=stdout)

        self.assertIn("espe: new=2 updated=0 skipped=0 errors=0", stdout.getvalue())
        self.assertEqual(Job.objects.count(), 2)


class FirstExampleCollector(ExampleCollector):
    name = "first"

    def collect(self):
        return [
            JobRecord(
                source=self.name,
                source_id="first-job",
                title="First Job",
                institution_name="Example University",
                source_url="https://example.edu/jobs/first",
            )
        ]


class SecondExampleCollector(ExampleCollector):
    name = "second"

    def collect(self):
        return [
            JobRecord(
                source=self.name,
                source_id="second-job",
                title="Second Job",
                institution_name="Example University",
                source_url="https://example.edu/jobs/second",
            )
        ]


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self.body.encode("utf-8")


class GenericHTMLCollectorTests(TestCase):
    def setUp(self):
        self.university = University.objects.create(
            name="Generic University",
            city="Quito",
            province="Pichincha",
            type=University.UniversityType.PUBLIC,
            website="https://example.edu",
            jobs_url="https://example.edu/jobs/",
        )
        self.collector_config = Collector.objects.create(
            university=self.university,
            name="generic-example",
            module_path="collectors.generic_html.GenericHTMLCollector",
            list_selector=".job-card",
            title_selector=".title",
            link_selector=".details",
            date_selector=".date",
            description_selector=".summary",
        )
        self.sample_html = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "generic_jobs_sample.html"
        ).read_text(encoding="utf-8")

    def test_css_selectors_parse_records_and_skip_missing_link(self):
        records = GenericHTMLCollector(
            collector_config=self.collector_config,
            fetcher=lambda url: self.sample_html,
        ).collect()

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].title, "Research Coordinator")
        self.assertEqual(records[0].source, "generic-example")
        self.assertEqual(records[0].source_url, "https://example.edu/careers/research-coordinator")
        self.assertEqual(records[0].description, "Coordinate applied research projects.")
        self.assertEqual(records[0].posted_date.isoformat(), "2026-10-15")
        self.assertEqual(records[0].raw_data["date_text"], "2026-10-15")

    def test_xpath_selectors_parse_records(self):
        self.collector_config.list_selector = "//article[contains(@class, 'job-card')]"
        self.collector_config.title_selector = ".//h2[contains(@class, 'title')]"
        self.collector_config.link_selector = ".//a[contains(@class, 'details')]"
        self.collector_config.description_selector = ".//p[contains(@class, 'summary')]"
        self.collector_config.save()

        records = GenericHTMLCollector(
            collector_config=self.collector_config,
            fetcher=lambda url: self.sample_html,
        ).collect()

        self.assertEqual(len(records), 2)
        self.assertEqual(records[1].source_url, "https://jobs.example.edu/data-science")

    def test_run_collectors_executes_generic_collector(self):
        stdout = StringIO()
        with patch("collectors.generic_html.urlopen", return_value=FakeResponse(self.sample_html)):
            call_command("run_collectors", "generic-example", stdout=stdout)

        self.assertIn("generic-example: new=2 updated=0 skipped=0 errors=0", stdout.getvalue())
        self.assertEqual(Job.objects.count(), 2)


class LinkFilterTests(SimpleTestCase):
    def test_ignores_documents_images_downloads_viewers_and_navigation(self):
        link_filter = LinkFilter()

        self.assertFalse(link_filter.allow("Convocatoria docente", "https://x.test/job.pdf"))
        self.assertFalse(link_filter.allow("Research job", "https://x.test/image.png"))
        self.assertFalse(link_filter.allow("Download vacancy", "https://x.test/download/job"))
        self.assertFalse(link_filter.allow("Viewer", "https://x.test/viewer?id=1"))
        self.assertFalse(link_filter.allow("Menu docentes", "https://x.test/menu"))

    def test_include_and_exclude_patterns_are_configurable(self):
        link_filter = LinkFilter(include_patterns="postdoc", exclude_patterns="archive")

        self.assertTrue(link_filter.allow("Postdoc in biology", "https://x.test/jobs/1"))
        self.assertFalse(link_filter.allow("Lecturer role", "https://x.test/jobs/2"))
        self.assertFalse(link_filter.allow("Postdoc archive", "https://x.test/archive/1"))

    def test_allowed_and_blocked_extensions_are_configurable(self):
        link_filter = LinkFilter(
            include_patterns="vacancy",
            allowed_extensions="html htm",
            blocked_extensions="xml",
        )

        self.assertTrue(link_filter.allow("Vacancy", "https://x.test/job.html"))
        self.assertTrue(link_filter.allow("Vacancy", "https://x.test/jobs/1"))
        self.assertFalse(link_filter.allow("Vacancy", "https://x.test/job.json"))
        self.assertFalse(link_filter.allow("Vacancy", "https://x.test/job.xml"))
        self.assertFalse(link_filter.allow("Vacancy", "https://x.test/job.pdf"))


class JobExtractorTests(SimpleTestCase):
    def test_resolves_normalizes_deduplicates_and_skips_navigation(self):
        page = """
            <nav><a href='/jobs/menu'> Research job menu </a></nav>
            <article><a href='../jobs/1'> Research   Fellow </a></article>
            <article><a href='https://example.edu/careers/jobs/1'>Duplicate job</a></article>
        """
        links = JobExtractor(base_url="https://example.edu/careers/list/").extract_links(page)

        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].title, "Research Fellow")
        self.assertEqual(links[0].url, "https://example.edu/careers/jobs/1")
