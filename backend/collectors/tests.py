from io import StringIO
import importlib
from datetime import date, timedelta
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from .base import BaseCollector
from .espe import ESPECollector
from .extraction import JobExtractor, LinkFilter
from .generic_html import GenericHTMLCollector
from .registry import CollectorRegistry, registry
from .retry import retry_with_backoff
from .types import JobRecord
from collectors.models import Collector, CollectorExecution, CollectorTemplate
from jobs.models import Job
from profiles.models import JobMatch, ResearcherProfile
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


class TimeoutCollector(BaseCollector):
    name = "timeout"

    def collect(self):
        raise TimeoutError("timed out after 30 seconds")


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

    def test_default_retries_transient_timeout(self):
        calls = []

        def operation():
            calls.append("called")
            raise TimeoutError("slow site")

        with self.assertRaises(TimeoutError):
            retry_with_backoff(operation, attempts=3, sleeper=lambda delay: None)

        self.assertEqual(len(calls), 3)

    def test_default_does_not_retry_non_network_error(self):
        calls = []

        def operation():
            calls.append("called")
            raise ValueError("bad parser")

        with self.assertRaises(ValueError):
            retry_with_backoff(operation, attempts=3, sleeper=lambda delay: None)

        self.assertEqual(len(calls), 1)

    def test_non_transient_http_error_is_not_retried(self):
        calls = []

        def operation():
            calls.append("called")
            raise HTTPError("https://example.edu", 404, "Not Found", {}, None)

        with self.assertRaises(HTTPError):
            retry_with_backoff(operation, attempts=3, sleeper=lambda delay: None)

        self.assertEqual(len(calls), 1)


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

    def test_collector_timeout_defaults_to_thirty_seconds(self):
        collector = Collector.objects.create(
            university=University.objects.get(name="Example University"),
            name="default-timeout",
            module_path="collectors.tests.ExampleCollector",
        )

        self.assertEqual(collector.timeout, 30)

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
        self.assertEqual(collector.health_status, Collector.HealthStatus.HEALTHY)
        self.assertEqual(collector.last_job_count, 1)
        self.assertIsNotNone(collector.last_duration)
        self.assertEqual(collector.last_error, "")

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

    def test_timeout_is_recorded_and_remaining_collectors_continue(self):
        university = University.objects.get(name="Example University")
        Collector.objects.create(
            university=university,
            name="timeout",
            module_path="collectors.tests.TimeoutCollector",
            priority=10,
        )
        Collector.objects.create(
            university=university,
            name="example",
            module_path="collectors.tests.ExampleCollector",
            priority=20,
        )
        stdout = StringIO()

        call_command("run_collectors", stdout=stdout)

        self.assertIn("timeout: new=0 updated=0 skipped=0 errors=1", stdout.getvalue())
        self.assertIn("example: new=1 updated=0 skipped=0 errors=0", stdout.getvalue())
        self.assertEqual(Job.objects.count(), 1)
        execution = CollectorExecution.objects.get(collector_name="timeout")
        self.assertEqual(execution.errors, 1)
        self.assertEqual(execution.error_reason, "Timeout: timed out after 30 seconds")


class RefreshJobsCommandTests(TestCase):
    def setUp(self):
        self.university = University.objects.create(
            name="Example University",
            city="Quito",
            province="Pichincha",
            type=University.UniversityType.PUBLIC,
            website="https://example.edu",
        )
        user = get_user_model().objects.create_user(username="refresh-user")
        self.profile = ResearcherProfile.objects.create(
            user=user,
            full_name="Refresh User",
        )

    @patch("collectors.management.commands.refresh_jobs.call_command")
    def test_invokes_existing_commands_in_order(self, mocked_call_command):
        invoked = []

        def run_command(name, **kwargs):
            invoked.append(name)
            if name == "compute_matches":
                kwargs["stdout"].write("Matches computed: created=0 updated=0")

        mocked_call_command.side_effect = run_command

        call_command("refresh_jobs", stdout=StringIO())

        self.assertEqual(invoked, ["run_collectors", "compute_matches"])

    def test_runs_collectors_then_matches_and_prints_totals(self):
        Collector.objects.create(
            university=self.university,
            name="example",
            module_path="collectors.tests.ExampleCollector",
        )
        job = Job.objects.create(
            university=self.university,
            source="example",
            external_id="job-1",
            title="Research Fellow",
            url="https://example.edu/jobs/1",
            status=Job.Status.ACTIVE,
        )
        stdout = StringIO()

        call_command("refresh_jobs", stdout=stdout)

        self.assertEqual(JobMatch.objects.filter(job=job, researcher_profile=self.profile).count(), 1)
        self.assertEqual(
            stdout.getvalue().splitlines(),
            [
                "example: new=0 updated=0 skipped=1 errors=0",
                "Collectors summary:",
                "- new: 0",
                "- updated: 0",
                "- skipped: 1",
                "- errors: 0",
                "Matches:",
                "- created: 1",
                "- updated: 0",
            ],
        )

    def test_collector_failure_does_not_stop_remaining_pipeline(self):
        Collector.objects.create(
            university=self.university,
            name="timeout",
            module_path="collectors.tests.TimeoutCollector",
            priority=10,
        )
        Collector.objects.create(
            university=self.university,
            name="example",
            module_path="collectors.tests.ExampleCollector",
            priority=20,
        )
        stdout = StringIO()

        call_command("refresh_jobs", stdout=stdout)

        output = stdout.getvalue()
        collector_lines = [line for line in output.splitlines() if line.startswith(("timeout:", "example:"))]
        self.assertEqual(len(collector_lines), 2)
        self.assertIn("error=Timeout: timed out after 30 seconds", collector_lines[0])
        self.assertIn("- new: 1", output)
        self.assertIn("- errors: 1", output)
        self.assertIn("Matches:", output)
        self.assertEqual(Job.objects.count(), 1)

    @patch("collectors.management.commands.refresh_jobs.call_command")
    def test_unexpected_internal_error_raises_command_error(self, mocked_call_command):
        mocked_call_command.side_effect = RuntimeError("database unavailable")

        with self.assertRaisesMessage(CommandError, "Job refresh failed: database unavailable"):
            call_command("refresh_jobs", stdout=StringIO())


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

    def test_http_request_uses_robust_defaults(self):
        with patch("collectors.espe.urlopen", return_value=FakeResponse(self.sample_html)) as mocked:
            ESPECollector()._fetch_url(self.university.jobs_url)

        request = mocked.call_args.args[0]
        self.assertEqual(mocked.call_args.kwargs["timeout"], 30)
        self.assertTrue(request.get_header("User-agent").startswith("CareerOS/"))
        self.assertIn("text/html", request.get_header("Accept"))
        self.assertIn("es", request.get_header("Accept-language"))

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

    def test_configured_http_timeout_is_used(self):
        self.collector_config.timeout = 47
        collector = GenericHTMLCollector(collector_config=self.collector_config)

        with patch("collectors.generic_html.urlopen", return_value=FakeResponse(self.sample_html)) as mocked:
            collector._fetch_url(self.university.jobs_url)

        self.assertEqual(mocked.call_args.kwargs["timeout"], 47)

    def test_expired_and_old_jobs_are_ignored(self):
        today = date.today()
        self.collector_config.date_selector = ".date"
        self.collector_config.deadline_selector = ".deadline"
        self.collector_config.max_age_days = 30
        page = f"""
            <article class='job-card'>
              <h2 class='title'>Research Fellow active</h2>
              <a class='details' href='/jobs/active'>Details</a>
              <span class='date'>{(today - timedelta(days=5)).isoformat()}</span>
              <span class='deadline'>{(today + timedelta(days=5)).isoformat()}</span>
            </article>
            <article class='job-card'>
              <h2 class='title'>Research Fellow expired</h2>
              <a class='details' href='/jobs/expired'>Details</a>
              <span class='date'>{(today - timedelta(days=5)).isoformat()}</span>
              <span class='deadline'>{(today - timedelta(days=1)).isoformat()}</span>
            </article>
            <article class='job-card'>
              <h2 class='title'>Research Fellow historical</h2>
              <a class='details' href='/jobs/old'>Details</a>
              <span class='date'>{(today - timedelta(days=31)).isoformat()}</span>
              <span class='deadline'>{(today + timedelta(days=5)).isoformat()}</span>
            </article>
        """

        records = GenericHTMLCollector(
            collector_config=self.collector_config,
            fetcher=lambda url: page,
        ).collect()

        self.assertEqual([record.title for record in records], ["Research Fellow active"])
        self.assertEqual(records[0].posted_date, today - timedelta(days=5))
        self.assertEqual(records[0].deadline_date, today + timedelta(days=5))

    def test_template_supplies_selector_configuration(self):
        template = CollectorTemplate.objects.create(
            name="Test cards",
            list_selector=".job-card",
            title_selector=".title",
            link_selector=".details",
            date_selector=".date",
            description_selector=".summary",
        )
        self.collector_config.template = template
        self.collector_config.list_selector = ""
        self.collector_config.title_selector = ""
        self.collector_config.link_selector = ""
        self.collector_config.date_selector = ""
        self.collector_config.description_selector = ""
        self.collector_config.full_clean()

        records = GenericHTMLCollector(
            collector_config=self.collector_config,
            fetcher=lambda url: self.sample_html,
        ).collect()

        self.assertEqual(len(records), 2)

    def test_generic_configuration_requires_valid_selectors(self):
        self.collector_config.list_selector = "div["

        with self.assertRaises(ValidationError):
            self.collector_config.full_clean()


class TestCollectorCommandTests(TestCase):
    def setUp(self):
        university = University.objects.create(
            name="Command University",
            city="Quito",
            province="Pichincha",
            type=University.UniversityType.PUBLIC,
            website="https://command.example.edu",
            jobs_url="https://command.example.edu/jobs/",
        )
        self.definition = Collector.objects.create(
            university=university,
            name="command-example",
            module_path="collectors.generic_html.GenericHTMLCollector",
            list_selector=".job-card",
            title_selector=".title",
            link_selector=".details",
        )
        self.page = """
            <article class='job-card'>
              <h2 class='title'>Research Fellow</h2>
              <a class='details' href='/jobs/fellow'>Details</a>
            </article>
        """

    def test_command_prints_jobs_without_persisting(self):
        stdout = StringIO()
        with patch("collectors.generic_html.urlopen", return_value=FakeResponse(self.page)):
            call_command("test_collector", "command-example", stdout=stdout)

        self.assertIn("Research Fellow | https://command.example.edu/jobs/fellow", stdout.getvalue())
        self.assertIn("Extracted 1 job(s).", stdout.getvalue())
        self.assertEqual(Job.objects.count(), 0)
        execution = CollectorExecution.objects.get(collector_name="command-example")
        self.assertEqual(execution.skipped, 1)
        self.assertEqual(execution.errors, 0)
        self.assertEqual(execution.error_reason, "")
        self.definition.refresh_from_db()
        self.assertEqual(self.definition.health_status, Collector.HealthStatus.HEALTHY)
        self.assertEqual(self.definition.last_job_count, 1)

    def test_command_reports_invalid_selector(self):
        self.definition.list_selector = "div["
        self.definition.save(update_fields=["list_selector"])

        with self.assertRaisesMessage(CommandError, "Collector test failed"):
            call_command("test_collector", "command-example")

        self.definition.refresh_from_db()
        self.assertEqual(self.definition.health_status, Collector.HealthStatus.ERROR)
        self.assertIn("Invalid selector", self.definition.last_error)
        execution = CollectorExecution.objects.get(collector_name="command-example")
        self.assertEqual(execution.errors, 1)
        self.assertIn("ValidationError", execution.error_reason)

    def test_command_reports_selector_with_no_matches(self):
        self.definition.list_selector = ".missing"
        self.definition.save(update_fields=["list_selector"])
        stderr = StringIO()
        with patch("collectors.generic_html.urlopen", return_value=FakeResponse(self.page)):
            call_command("test_collector", "command-example", stderr=stderr)

        self.assertIn("Selector matched no elements: .missing", stderr.getvalue())
        self.definition.refresh_from_db()
        self.assertEqual(self.definition.health_status, Collector.HealthStatus.EMPTY)
        self.assertEqual(self.definition.last_job_count, 0)
        execution = CollectorExecution.objects.get(collector_name="command-example")
        self.assertEqual(execution.skipped, 0)
        self.assertEqual(execution.errors, 0)


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

    def test_parses_spanish_and_relative_dates(self):
        today = date(2026, 9, 25)

        self.assertEqual(
            JobExtractor.parse_date("Publicado: 19 de agosto, 2026"),
            date(2026, 8, 19),
        )
        self.assertEqual(
            JobExtractor.parse_date("Hace 7 días", today=today),
            date(2026, 9, 18),
        )


class FirstUniversitiesConfigurationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        names = [
            "Universidad San Francisco de Quito",
            "Pontificia Universidad Catolica del Ecuador",
            "Escuela Superior Politecnica del Litoral",
            "Escuela Politecnica Nacional",
            "Universidad Tecnica Particular de Loja",
        ]
        for index, name in enumerate(names):
            University.objects.create(
                name=name,
                city="Test City",
                province="Test Province",
                type="public",
                website=f"https://university-{index}.example",
            )
        migration = importlib.import_module(
            "collectors.migrations.0009_collector_deadline_selector_collector_max_age_days_and_more"
        )
        from django.apps import apps

        migration.configure_first_universities(apps, None)

    def test_target_universities_have_generic_collectors(self):
        expected = {"usfq", "puce", "espol", "epn", "utpl"}
        collectors = Collector.objects.filter(name__in=expected).select_related("university", "template")

        self.assertEqual({collector.name for collector in collectors}, expected)
        for collector in collectors:
            self.assertEqual(
                collector.module_path,
                "collectors.generic_html.GenericHTMLCollector",
            )
            self.assertTrue(collector.university.jobs_url)
            self.assertIsNotNone(collector.template)
            self.assertEqual(collector.max_age_days, 30)
            collector.full_clean()


class VS019UDLAConfigurationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        University.objects.create(
            name="Universidad de Las Americas",
            city="Distrito Metropolitano de Quito",
            province="Pichincha",
            type=University.UniversityType.PRIVATE_SELFFINANCED,
            website="https://www.udla.edu.ec",
        )
        migration = importlib.import_module(
            "collectors.migrations.0010_seed_vs019_udla_collector"
        )
        from django.apps import apps

        migration.configure_vs019_udla(apps, None)

    def test_udla_uses_reusable_generic_template_and_thirty_day_filter(self):
        collector = Collector.objects.select_related("university", "template").get(name="udla")

        self.assertEqual(
            collector.module_path,
            "collectors.generic_html.GenericHTMLCollector",
        )
        self.assertEqual(
            collector.university.jobs_url,
            "https://empleos.udla.edu.ec/search/?q=&locationsearch=",
        )
        self.assertEqual(collector.template.name, "SAP SuccessFactors job results")
        self.assertEqual(collector.max_age_days, 30)
        collector.full_clean()

    def test_udla_selectors_extract_successfactors_results(self):
        collector = Collector.objects.get(name="udla")
        page = """
            <table id="searchresults"><tbody>
              <tr class="data-row">
                <td class="colTitle">
                  <span class="jobTitle hidden-phone">
                    <a class="jobTitle-link" href="/job/QUITO-DOCENTE/123/">Docente de Física</a>
                  </span>
                </td>
                <td class="colLocation hidden-phone"><span class="jobLocation">QUITO, ECUADOR</span></td>
                <td class="colDate hidden-phone"><span class="jobDate">26 sept 2026</span></td>
                <td class="colDepartment hidden-phone"><span class="jobDepartment">Académicos</span></td>
              </tr>
            </tbody></table>
        """

        records = GenericHTMLCollector(
            collector_config=collector,
            fetcher=lambda url: page,
        ).collect()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].title, "Docente de Física")
        self.assertEqual(
            records[0].source_url,
            "https://empleos.udla.edu.ec/job/QUITO-DOCENTE/123/",
        )
        self.assertIn("Académicos", records[0].description)
