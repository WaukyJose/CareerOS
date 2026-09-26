from datetime import timedelta

from django.db import IntegrityError, transaction
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from dashboard.services import DashboardService
from jobs.models import Job
from profiles.models import ResearcherProfile
from universities.models import University

from .models import Application


class ApplicationFixtureMixin:
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username="application-user", password="test-pass")
        self.other_user = get_user_model().objects.create_user(username="other-application-user", password="test-pass")
        self.client.force_authenticate(self.user)
        self.alpha = University.objects.create(
            name="Alpha University",
            city="Quito",
            province="Pichincha",
            type=University.UniversityType.PUBLIC,
            website="https://alpha.example",
        )
        self.beta = University.objects.create(
            name="Beta University",
            city="Guayaquil",
            province="Guayas",
            type=University.UniversityType.PUBLIC,
            website="https://beta.example",
        )
        self.job = self.create_job(self.alpha, "alpha")
        self.other_job = self.create_job(self.beta, "beta")
        self.profile = ResearcherProfile.objects.create(user=self.user, full_name="Ada")
        self.other_profile = ResearcherProfile.objects.create(user=self.other_user, full_name="Grace")

    @staticmethod
    def create_job(university, external_id):
        return Job.objects.create(
            university=university,
            source="application-test",
            external_id=external_id,
            title=f"Job {external_id}",
            url=f"https://example.test/{external_id}",
            status=Job.Status.ACTIVE,
        )


class ApplicationModelTests(ApplicationFixtureMixin, TestCase):
    def test_status_transitions_set_milestone_timestamps(self):
        application = Application.objects.create(
            researcher_profile=self.profile,
            job=self.job,
        )
        self.assertIsNotNone(application.saved_at)

        for status, field in (
            (Application.Status.APPLIED, "applied_at"),
            (Application.Status.INTERVIEW, "interview_at"),
            (Application.Status.OFFER, "offer_at"),
            (Application.Status.ACCEPTED, "accepted_at"),
        ):
            application.status = status
            application.save(update_fields=["status"])
            self.assertIsNotNone(getattr(application, field))
        application.refresh_from_db()
        self.assertIsNotNone(application.applied_at)
        self.assertIsNotNone(application.interview_at)
        self.assertIsNotNone(application.offer_at)
        self.assertIsNotNone(application.accepted_at)

    def test_database_prevents_duplicate_profile_job_application(self):
        Application.objects.create(researcher_profile=self.profile, job=self.job)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Application.objects.create(researcher_profile=self.profile, job=self.job)

    def test_dashboard_application_metrics_are_cumulative(self):
        accepted = Application.objects.create(researcher_profile=self.profile, job=self.job)
        for status in (
            Application.Status.APPLIED,
            Application.Status.INTERVIEW,
            Application.Status.OFFER,
            Application.Status.ACCEPTED,
        ):
            accepted.status = status
            accepted.save()
        rejected = Application.objects.create(
            researcher_profile=self.other_profile,
            job=self.other_job,
        )
        rejected.status = Application.Status.APPLIED
        rejected.save()
        rejected.status = Application.Status.REJECTED
        rejected.save()
        third_job = self.create_job(self.alpha, "saved")
        Application.objects.create(researcher_profile=self.profile, job=third_job)

        summary = DashboardService.summary()

        self.assertEqual(summary["saved_jobs"], 3)
        self.assertEqual(summary["applied_jobs"], 2)
        self.assertEqual(summary["interviews"], 1)
        self.assertEqual(summary["offers"], 1)
        self.assertEqual(summary["accepted"], 1)


class ApplicationAPITests(ApplicationFixtureMixin, TestCase):
    def test_crud(self):
        create_response = self.client.post(
            "/api/applications/",
            {
                "researcher_profile": self.profile.id,
                "job": self.job.id,
                "status": Application.Status.SAVED,
                "notes": "Review later",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 201)
        application_id = create_response.data["id"]

        list_response = self.client.get("/api/applications/")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.data["count"], 1)

        patch_response = self.client.patch(
            f"/api/applications/{application_id}/",
            {"status": Application.Status.APPLIED, "notes": "Submitted"},
            format="json",
        )
        self.assertEqual(patch_response.status_code, 200)
        self.assertIsNotNone(patch_response.data["applied_at"])
        self.assertEqual(patch_response.data["notes"], "Submitted")

        delete_response = self.client.delete(f"/api/applications/{application_id}/")
        self.assertEqual(delete_response.status_code, 204)
        self.assertFalse(Application.objects.exists())

    def test_invalid_backward_status_transition_is_rejected(self):
        application = Application.objects.create(
            researcher_profile=self.profile,
            job=self.job,
            status=Application.Status.APPLIED,
        )

        response = self.client.patch(
            f"/api/applications/{application.id}/",
            {"status": Application.Status.SAVED},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        application.refresh_from_db()
        self.assertEqual(application.status, Application.Status.APPLIED)

    def test_duplicate_creation_returns_validation_error(self):
        Application.objects.create(researcher_profile=self.profile, job=self.job)

        response = self.client.post(
            "/api/applications/",
            {"researcher_profile": self.profile.id, "job": self.job.id},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Application.objects.count(), 1)

    def test_filters_by_profile_status_and_university(self):
        target = Application.objects.create(
            researcher_profile=self.profile,
            job=self.job,
            status=Application.Status.APPLIED,
        )
        Application.objects.create(
            researcher_profile=self.other_profile,
            job=self.other_job,
            status=Application.Status.SAVED,
        )

        response = self.client.get(
            "/api/applications/",
            {
                "profile": self.profile.id,
                "status": "applied",
                "university": self.alpha.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], target.id)

    def test_orders_by_newest_and_applied_at(self):
        older = Application.objects.create(
            researcher_profile=self.profile,
            job=self.job,
            status=Application.Status.APPLIED,
        )
        newer = Application.objects.create(
            researcher_profile=self.profile,
            job=self.other_job,
            status=Application.Status.APPLIED,
        )
        now = timezone.now()
        Application.objects.filter(pk=older.pk).update(
            saved_at=now - timedelta(days=2),
            applied_at=now,
        )
        Application.objects.filter(pk=newer.pk).update(
            saved_at=now,
            applied_at=now - timedelta(days=1),
        )

        newest = self.client.get("/api/applications/", {"ordering": "newest"})
        applied = self.client.get("/api/applications/", {"ordering": "applied_at"})

        self.assertEqual(
            [item["id"] for item in newest.data["results"]],
            [newer.id, older.id],
        )
        self.assertEqual(
            [item["id"] for item in applied.data["results"]],
            [older.id, newer.id],
        )
