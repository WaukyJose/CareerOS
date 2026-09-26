from datetime import timedelta

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from jobs.models import Job
from profiles.models import JobMatch, ResearcherProfile
from universities.models import University

from .services import DashboardService


class DashboardFixtureMixin:
    def create_university(self):
        return University.objects.create(
            name="Dashboard University",
            city="Quito",
            province="Pichincha",
            type=University.UniversityType.PUBLIC,
            website="https://dashboard.example",
        )

    def create_job(self, university, external_id, **overrides):
        values = {
            "source": "dashboard-test",
            "external_id": external_id,
            "title": f"Job {external_id}",
            "url": f"https://dashboard.example/jobs/{external_id}",
            "status": Job.Status.ACTIVE,
        }
        values.update(overrides)
        return Job.objects.create(university=university, **values)

    @staticmethod
    def create_profile(full_name):
        user = get_user_model().objects.create_user(
            username=f"dashboard-profile-{ResearcherProfile.objects.count() + 1}"
        )
        return ResearcherProfile.objects.create(user=user, full_name=full_name)


class DashboardServiceTests(DashboardFixtureMixin, TestCase):
    def test_empty_database_returns_zero_metrics_and_empty_results(self):
        self.assertEqual(
            DashboardService.summary(),
            {
                "total_jobs": 0,
                "active_jobs": 0,
                "matched_jobs": 0,
                "saved_jobs": 0,
                "applied_jobs": 0,
                "interviews": 0,
                "offers": 0,
                "accepted": 0,
                "closing_soon": 0,
                "new_jobs_last_7_days": 0,
                "average_match_score": 0,
                "top_match_score": 0,
            },
        )
        self.assertEqual(list(DashboardService.top_matches()), [])
        self.assertEqual(list(DashboardService.recent_jobs()), [])
        self.assertEqual(list(DashboardService.closing_soon()), [])

    def test_populated_database_statistics_are_correct(self):
        university = self.create_university()
        today = timezone.localdate()
        near = self.create_job(university, "near", deadline_date=today + timedelta(days=3))
        later = self.create_job(university, "later", deadline_date=today + timedelta(days=20))
        closed = self.create_job(
            university,
            "closed",
            status=Job.Status.CLOSED,
            deadline_date=today + timedelta(days=2),
        )
        Job.objects.filter(pk=closed.pk).update(created_at=timezone.now() - timedelta(days=8))
        first = self.create_profile("First")
        second = self.create_profile("Second")
        JobMatch.objects.create(job=near, researcher_profile=first, score=90, matched=True)
        JobMatch.objects.create(job=later, researcher_profile=first, score=50, matched=False)
        JobMatch.objects.create(job=near, researcher_profile=second, score=70, matched=True)

        summary = DashboardService.summary()

        self.assertEqual(summary["total_jobs"], 3)
        self.assertEqual(summary["active_jobs"], 2)
        self.assertEqual(summary["matched_jobs"], 1)
        self.assertEqual(summary["saved_jobs"], 0)
        self.assertEqual(summary["applied_jobs"], 0)
        self.assertEqual(summary["closing_soon"], 1)
        self.assertEqual(summary["new_jobs_last_7_days"], 2)
        self.assertEqual(summary["average_match_score"], 70)
        self.assertEqual(summary["top_match_score"], 90)

    def test_recent_jobs_are_limited_to_seven_days_and_ordered_newest(self):
        university = self.create_university()
        newest = self.create_job(university, "newest")
        recent = self.create_job(university, "recent")
        old = self.create_job(university, "old")
        now = timezone.now()
        Job.objects.filter(pk=newest.pk).update(created_at=now)
        Job.objects.filter(pk=recent.pk).update(created_at=now - timedelta(days=2))
        Job.objects.filter(pk=old.pk).update(created_at=now - timedelta(days=8))

        jobs = list(DashboardService.recent_jobs())

        self.assertEqual([job.id for job in jobs], [newest.id, recent.id])

    def test_closing_soon_excludes_closed_past_and_later_jobs_and_orders_deadlines(self):
        university = self.create_university()
        today = timezone.localdate()
        second = self.create_job(university, "second", deadline_date=today + timedelta(days=10))
        first = self.create_job(university, "first", deadline_date=today + timedelta(days=2))
        self.create_job(university, "past", deadline_date=today - timedelta(days=1))
        self.create_job(university, "later", deadline_date=today + timedelta(days=15))
        self.create_job(
            university,
            "closed",
            deadline_date=today + timedelta(days=1),
            status=Job.Status.CLOSED,
        )

        jobs = list(DashboardService.closing_soon())

        self.assertEqual([job.id for job in jobs], [first.id, second.id])

    def test_top_matches_defaults_to_twenty_and_orders_score_descending(self):
        university = self.create_university()
        job = self.create_job(university, "ranked")
        for score in range(1, 22):
            profile = self.create_profile(f"Profile {score}")
            JobMatch.objects.create(
                job=job,
                researcher_profile=profile,
                score=score,
                matched=True,
            )

        matches = list(DashboardService.top_matches())

        self.assertEqual(len(matches), 20)
        self.assertEqual([match.score for match in matches], list(range(21, 1, -1)))


class DashboardAPITests(DashboardFixtureMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username="dashboard-user", password="test-pass")
        self.client.force_authenticate(self.user)
        self.university = self.create_university()
        today = timezone.localdate()
        self.job = self.create_job(
            self.university,
            "api",
            deadline_date=today + timedelta(days=5),
        )
        self.profile = ResearcherProfile.objects.create(user=self.user, full_name="API Profile")
        self.match = JobMatch.objects.create(
            job=self.job,
            researcher_profile=self.profile,
            score=88,
            matched=True,
        )

    def test_summary_endpoint(self):
        response = self.client.get("/api/dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_jobs"], 1)
        self.assertEqual(response.data["top_match_score"], 88)

    def test_dashboard_collection_endpoints(self):
        cases = (
            ("/api/dashboard/top-matches/", self.match.id),
            ("/api/dashboard/recent/", self.job.id),
            ("/api/dashboard/closing-soon/", self.job.id),
        )
        for url, expected_id in cases:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data[0]["id"], expected_id)
