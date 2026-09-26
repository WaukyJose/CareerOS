from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from applications.models import Application
from jobs.models import Job
from universities.models import University

from .models import JobMatch, ResearcherProfile


class AuthenticationAndIsolationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="ada", password="secure-pass")
        self.other_user = user_model.objects.create_user(username="grace", password="other-pass")
        self.profile = ResearcherProfile.objects.create(user=self.user, full_name="Ada")
        self.other_profile = ResearcherProfile.objects.create(user=self.other_user, full_name="Grace")
        self.university = University.objects.create(
            name="Auth University",
            city="Quito",
            province="Pichincha",
            type=University.UniversityType.PUBLIC,
            website="https://auth.example",
        )
        self.job = self._job("one")
        self.other_job = self._job("two")
        self.match = JobMatch.objects.create(
            job=self.job,
            researcher_profile=self.profile,
            score=90,
            matched=True,
        )
        self.other_match = JobMatch.objects.create(
            job=self.other_job,
            researcher_profile=self.other_profile,
            score=99,
            matched=True,
        )
        self.application = Application.objects.create(
            job=self.job,
            researcher_profile=self.profile,
        )
        self.other_application = Application.objects.create(
            job=self.other_job,
            researcher_profile=self.other_profile,
        )

    def test_unauthorized_api_access_is_denied(self):
        client = APIClient()

        for url in (
            "/api/jobs/",
            "/api/profile/",
            "/api/matches/",
            "/api/applications/",
            "/api/dashboard/",
            "/api/dashboard/top-matches/",
            "/api/dashboard/recent/",
            "/api/dashboard/closing-soon/",
        ):
            with self.subTest(url=url):
                self.assertEqual(client.get(url).status_code, 401)

    def test_token_authentication_allows_access(self):
        response = APIClient().post(
            "/api/token/",
            {"username": "ada", "password": "secure-pass"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        token = response.data["token"]
        self.assertEqual(token, Token.objects.get(user=self.user).key)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(client.get("/api/profile/").status_code, 200)

    def test_users_only_see_their_profile_matches_applications_and_dashboard(self):
        client = APIClient()
        client.force_authenticate(self.user)

        profile_response = client.get("/api/profile/")
        matches_response = client.get("/api/matches/")
        applications_response = client.get("/api/applications/")
        dashboard_response = client.get("/api/dashboard/")
        top_matches_response = client.get("/api/dashboard/top-matches/")

        self.assertEqual(profile_response.data["id"], self.profile.id)
        self.assertEqual(
            [item["id"] for item in matches_response.data["results"]],
            [self.match.id],
        )
        self.assertEqual(
            [item["id"] for item in applications_response.data["results"]],
            [self.application.id],
        )
        self.assertEqual(dashboard_response.data["matched_jobs"], 1)
        self.assertEqual(dashboard_response.data["saved_jobs"], 1)
        self.assertEqual(dashboard_response.data["top_match_score"], 90)
        self.assertEqual(
            [item["id"] for item in top_matches_response.data],
            [self.match.id],
        )

    def test_profile_and_application_crud_permissions(self):
        client = APIClient()
        client.force_authenticate(self.user)

        profile_response = client.patch(
            "/api/profile/",
            {"city": "Cuenca"},
            format="json",
        )
        self.assertEqual(profile_response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.city, "Cuenca")
        self.other_profile.refresh_from_db()
        self.assertNotEqual(self.other_profile.city, "Cuenca")

        forbidden_patch = client.patch(
            f"/api/applications/{self.other_application.id}/",
            {"notes": "not allowed"},
            format="json",
        )
        forbidden_delete = client.delete(
            f"/api/applications/{self.other_application.id}/"
        )
        forbidden_create = client.post(
            "/api/applications/",
            {
                "researcher_profile": self.other_profile.id,
                "job": self.job.id,
            },
            format="json",
        )

        self.assertEqual(forbidden_patch.status_code, 404)
        self.assertEqual(forbidden_delete.status_code, 404)
        self.assertEqual(forbidden_create.status_code, 400)
        self.other_application.refresh_from_db()
        self.assertEqual(self.other_application.notes, "")

    def _job(self, external_id):
        return Job.objects.create(
            university=self.university,
            source="auth-test",
            external_id=external_id,
            title=f"Job {external_id}",
            url=f"https://auth.example/{external_id}",
            status=Job.Status.ACTIVE,
        )
