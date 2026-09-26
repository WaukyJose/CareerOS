from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch

from collectors.types import JobRecord
from universities.models import University

from .models import Job
from .enrichment import JobEnrichmentService
from .serializers import JobSerializer
from .services import JobService


class JobServiceTests(TestCase):
    def setUp(self):
        self.university = University.objects.create(
            name="Example University",
            city="Quito",
            province="Pichincha",
            type=University.UniversityType.PUBLIC,
            website="https://example.edu",
        )

    def test_upsert_creates_new_job(self):
        result = JobService.upsert(self._record())

        self.assertTrue(result.created)
        self.assertEqual(Job.objects.count(), 1)
        self.assertEqual(result.job.status, Job.Status.NEW)
        self.assertEqual(result.job.university, self.university)

    def test_upsert_skips_unchanged_job(self):
        JobService.upsert(self._record())

        result = JobService.upsert(self._record())

        self.assertTrue(result.skipped)
        self.assertEqual(Job.objects.count(), 1)

    def test_upsert_updates_modified_job(self):
        JobService.upsert(self._record(title="Original Title"))

        result = JobService.upsert(self._record(title="Updated Title"))

        self.assertTrue(result.updated)
        self.assertEqual(Job.objects.get().title, "Updated Title")

    def test_upsert_reactivates_closed_modified_job(self):
        JobService.upsert(self._record(title="Original Title"))
        job = Job.objects.get()
        job.status = Job.Status.CLOSED
        job.save(update_fields=["status"])

        result = JobService.upsert(self._record(title="Updated Title"))

        self.assertTrue(result.updated)
        self.assertEqual(result.job.status, Job.Status.ACTIVE)

    def test_database_rejects_duplicate_source_external_id(self):
        JobService.upsert(self._record())

        with self.assertRaises(IntegrityError):
            Job.objects.create(
                university=self.university,
                source="example",
                external_id="job-1",
                title="Duplicate",
                url="https://example.edu/jobs/duplicate",
            )

    def test_upsert_enriches_and_normalizes_collected_job(self):
        record = JobRecord(
            source="example",
            source_id="enriched-job",
            title="AI Research Scientist",
            institution_name=self.university.name,
            source_url="https://example.edu/jobs/enriched",
            department="  Department of Computing  ",
            employment_type="Tiempo Completo",
            description=(
                "Doctorado required. Permanent remote role. Salary: $2,500. "
                "Bilingual English and Spanish. Machine learning and Python research."
            ),
        )

        job = JobService.upsert(record).job

        self.assertEqual(job.discipline, "Artificial Intelligence")
        self.assertEqual(job.department, "Department of Computing")
        self.assertEqual(job.required_degree, "PhD")
        self.assertEqual(job.employment_type, "Full-time")
        self.assertEqual(job.salary, "$2,500")
        self.assertEqual(job.contract_type, "Permanent")
        self.assertEqual(job.language, "English and Spanish")
        self.assertTrue(job.remote)
        self.assertEqual(
            job.keywords,
            ["Artificial Intelligence", "Machine Learning", "Python", "Research"],
        )

    def test_enrichment_runs_on_create_and_change_but_not_unchanged_upsert(self):
        original = self._record(title="Research Fellow")
        changed = self._record(title="Senior Research Fellow")

        with patch.object(
            JobEnrichmentService,
            "enrich",
            wraps=JobEnrichmentService.enrich,
        ) as enrich:
            JobService.upsert(original)
            JobService.upsert(original)
            JobService.upsert(changed)

        self.assertEqual(enrich.call_count, 2)

    def test_changed_job_recomputes_enriched_values(self):
        original = JobRecord(
            source="example",
            source_id="job-degree",
            title="Research Fellow",
            institution_name=self.university.name,
            source_url="https://example.edu/jobs/degree",
            description="PhD required.",
        )
        changed = JobRecord(
            source="example",
            source_id="job-degree",
            title="Research Fellow",
            institution_name=self.university.name,
            source_url="https://example.edu/jobs/degree",
            description="Master's degree required.",
        )
        JobService.upsert(original)

        result = JobService.upsert(changed)

        self.assertTrue(result.updated)
        self.assertEqual(result.job.required_degree, "Master's")

    def _record(self, title="Research Fellow"):
        return JobRecord(
            source="example",
            source_id="job-1",
            title=title,
            institution_name=self.university.name,
            source_url="https://example.edu/jobs/1",
            location="Quito, Pichincha",
            raw_data={"source": "fixture"},
        )


class JobSerializerTests(TestCase):
    def test_serializer_includes_university_fields(self):
        university = University.objects.create(
            name="Example University",
            city="Quito",
            province="Pichincha",
            type=University.UniversityType.PUBLIC,
            website="https://example.edu",
        )
        job = Job.objects.create(
            university=university,
            source="example",
            external_id="job-1",
            title="Research Fellow",
            description="AI research role",
            url="https://example.edu/jobs/1",
        )

        data = JobSerializer(job).data

        self.assertEqual(data["university"], "Example University")
        self.assertEqual(data["university_id"], university.id)
        self.assertEqual(data["city"], "Quito")
        self.assertEqual(data["province"], "Pichincha")


class JobAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username="jobs-user", password="test-pass")
        self.client.force_authenticate(self.user)
        self.pichincha = University.objects.create(
            name="Alpha University",
            city="Quito",
            province="Pichincha",
            type=University.UniversityType.PUBLIC,
            website="https://alpha.edu",
        )
        self.guayas = University.objects.create(
            name="Beta University",
            city="Guayaquil",
            province="Guayas",
            type=University.UniversityType.PUBLIC,
            website="https://beta.edu",
        )
        self.alpha_job = self._job(
            university=self.pichincha,
            source="espe",
            external_id="alpha-1",
            title="AI Research Fellow",
            description="Machine learning and systems research",
            status=Job.Status.NEW,
            deadline_date="2026-12-15",
        )
        self.beta_job = self._job(
            university=self.guayas,
            source="manual",
            external_id="beta-1",
            title="Biology Lecturer",
            description="Teaching and lab coordination",
            status=Job.Status.ACTIVE,
            deadline_date="2026-10-01",
        )

    def test_list_jobs_is_paginated(self):
        response = self.client.get("/api/jobs/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 2)

    def test_retrieve_job_detail(self):
        response = self.client.get(f"/api/jobs/{self.alpha_job.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "AI Research Fellow")

    def test_filters_by_university_province_city_status_source_and_query(self):
        response = self.client.get(
            "/api/jobs/",
            {
                "university": "Alpha",
                "province": "Pichincha",
                "city": "Quito",
                "status": Job.Status.NEW,
                "source": "espe",
                "q": "machine",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.alpha_job.id)

    def test_ordering_by_deadline(self):
        response = self.client.get("/api/jobs/", {"ordering": "deadline"})

        self.assertEqual(response.status_code, 200)
        ids = [job["id"] for job in response.data["results"]]
        self.assertEqual(ids, [self.beta_job.id, self.alpha_job.id])

    def test_ordering_by_university(self):
        response = self.client.get("/api/jobs/", {"ordering": "university"})

        self.assertEqual(response.status_code, 200)
        universities = [job["university"] for job in response.data["results"]]
        self.assertEqual(universities, ["Alpha University", "Beta University"])

    def test_post_is_not_allowed(self):
        response = self.client.post(
            "/api/jobs/",
            {
                "title": "Unauthorized",
                "source": "manual",
                "external_id": "manual-1",
                "url": "https://example.edu/jobs/manual-1",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 405)

    def _job(
        self,
        *,
        university,
        source,
        external_id,
        title,
        description,
        status,
        deadline_date,
    ):
        return Job.objects.create(
            university=university,
            source=source,
            external_id=external_id,
            title=title,
            description=description,
            status=status,
            url=f"https://example.edu/jobs/{external_id}",
            deadline_date=deadline_date,
        )
