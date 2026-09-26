from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from jobs.models import Job
from universities.models import University

from .models import JobMatch, JobRole, ResearcherProfile, ResearchInterest


class ComputeMatchesCommandTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="compute-user")
        self.university = University.objects.create(
            name="Alpha University",
            city="Quito",
            province="Pichincha",
            type=University.UniversityType.PUBLIC,
            website="https://alpha.example",
        )
        self.job = Job.objects.create(
            university=self.university,
            source="test",
            external_id="active-job",
            title="AI Research Fellow",
            description="Artificial Intelligence research. PhD required.",
            discipline="Artificial Intelligence",
            required_degree="PhD",
            keywords=["Artificial Intelligence", "Research"],
            employment_type="Full time",
            location="Quito",
            url="https://alpha.example/jobs/1",
            status=Job.Status.ACTIVE,
        )
        self.profile = ResearcherProfile.objects.create(
            user=self.user,
            full_name="Ada Researcher",
            highest_degree="PhD",
            preferred_employment_types=["Full time"],
            preferred_locations=["Quito"],
            minimum_match_score=50,
        )
        interest = ResearchInterest.objects.create(name="Artificial Intelligence", weight=1)
        self.profile.research_interests.add(interest)
        self.role = JobRole.objects.get(name="Researcher")
        self.profile.preferred_roles.add(self.role)

    def test_command_creates_match_for_active_job_and_profile(self):
        inactive_job = Job.objects.create(
            university=self.university,
            source="test",
            external_id="new-job",
            title="Researcher",
            url="https://alpha.example/jobs/2",
            status=Job.Status.NEW,
        )
        inactive_profile = ResearcherProfile.objects.create(
            user=get_user_model().objects.create_user(username="inactive-compute-user"),
            full_name="Inactive Researcher",
            is_active=False,
        )

        call_command("compute_matches")

        match = JobMatch.objects.get()
        self.assertEqual(match.job, self.job)
        self.assertEqual(match.researcher_profile, self.profile)
        self.assertEqual(match.matched_role, self.role)
        self.assertTrue(match.matched)
        self.assertIn("summary", match.explanation)
        self.assertFalse(JobMatch.objects.filter(job=inactive_job).exists())
        self.assertFalse(JobMatch.objects.filter(researcher_profile=inactive_profile).exists())

    def test_command_updates_existing_match_after_profile_change(self):
        call_command("compute_matches")
        original = JobMatch.objects.get()
        original_score = original.score
        self.profile.preferred_roles.clear()
        self.profile.research_interests.clear()
        self.profile.preferred_employment_types = []
        self.profile.preferred_locations = []
        self.profile.save()

        call_command("compute_matches")

        updated = JobMatch.objects.get()
        self.assertLess(updated.score, original_score)
        self.assertIsNone(updated.matched_role)
        self.assertEqual(JobMatch.objects.count(), 1)

    def test_recomputation_reports_update_without_creating_duplicate(self):
        call_command("compute_matches")
        output = StringIO()

        call_command("compute_matches", stdout=output)

        self.assertIn("created=0 updated=1", output.getvalue())
        self.assertEqual(JobMatch.objects.count(), 1)

    def test_database_prevents_duplicate_profile_job_pair(self):
        JobMatch.objects.create(
            job=self.job,
            researcher_profile=self.profile,
            score=50,
            matched=True,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            JobMatch.objects.create(
                job=self.job,
                researcher_profile=self.profile,
                score=60,
                matched=True,
            )


class JobMatchAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username="match-user", password="test-pass")
        self.other_user = get_user_model().objects.create_user(username="other-match-user", password="test-pass")
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
        self.profile = ResearcherProfile.objects.create(user=self.user, full_name="Ada", minimum_match_score=50)
        self.other_profile = ResearcherProfile.objects.create(user=self.other_user, full_name="Grace", minimum_match_score=50)
        self.high = self._match(self.alpha, self.profile, 90, True, "high")
        self.medium = self._match(self.beta, self.profile, 60, True, "medium")
        self.low = self._match(self.alpha, self.other_profile, 30, False, "low")

    def test_filters_by_profile_score_matched_and_university(self):
        response = self.client.get(
            "/api/matches/",
            {
                "profile": self.profile.id,
                "minimum_score": 80,
                "matched_only": "true",
                "university": self.alpha.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.high.id)

    def test_orders_by_score_and_newest(self):
        score_response = self.client.get("/api/matches/", {"ordering": "score"})
        self.assertEqual(
            [item["id"] for item in score_response.data["results"]],
            [self.high.id, self.medium.id],
        )

        JobMatch.objects.filter(pk=self.low.pk).update(computed_at=timezone.now() + timedelta(days=1))
        newest_response = self.client.get("/api/matches/", {"ordering": "newest"})
        self.assertEqual(newest_response.data["results"][0]["id"], self.medium.id)

    def _match(self, university, profile, score, matched, external_id):
        job = Job.objects.create(
            university=university,
            source="api-test",
            external_id=external_id,
            title=f"Job {external_id}",
            url=f"https://example.test/{external_id}",
            status=Job.Status.ACTIVE,
        )
        return JobMatch.objects.create(
            job=job,
            researcher_profile=profile,
            score=score,
            matched=matched,
            explanation={"summary": external_id, "missing": []},
        )
