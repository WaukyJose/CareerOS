from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.test import TestCase

from jobs.models import Job
from universities.models import University

from .models import JobRole, PreferredInstitution, ResearcherProfile, ResearchInterest
from .services import MatchService


class ResearcherProfileModelTests(TestCase):
    def test_minimum_match_score_must_be_between_zero_and_one_hundred(self):
        profile = ResearcherProfile(full_name="Ada Researcher", minimum_match_score=101)

        with self.assertRaises(ValidationError):
            profile.full_clean()


class JobRoleSeedTests(TestCase):
    def test_seed_migration_creates_all_required_roles(self):
        self.assertEqual(JobRole.objects.count(), 29)
        self.assertEqual(
            set(JobRole.objects.values_list("category", flat=True)),
            set(JobRole.Category.values),
        )
        researcher = JobRole.objects.get(name="Researcher")
        self.assertEqual(researcher.category, JobRole.Category.RESEARCH)
        self.assertIn("Research Fellow", researcher.aliases)
        self.assertTrue(researcher.is_active)


class MatchServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="match-service-user")
        self.university = University.objects.create(
            name="Example University",
            city="Quito",
            province="Pichincha",
            type=University.UniversityType.PUBLIC,
            website="https://example.edu",
        )
        self.other_university = University.objects.create(
            name="Other University",
            city="Guayaquil",
            province="Guayas",
            type=University.UniversityType.PUBLIC,
            website="https://other.edu",
        )
        self.profile = ResearcherProfile.objects.create(
            user=self.user,
            full_name="Ada Researcher",
            highest_degree="PhD",
            current_position="Researcher",
            country="Ecuador",
            city="Quito",
            preferred_employment_types=["Full time"],
            preferred_locations=["Quito"],
            minimum_match_score=70,
        )
        self.ai = ResearchInterest.objects.create(name="Artificial Intelligence", weight=3)
        self.biology = ResearchInterest.objects.create(name="Biology", weight=1)
        self.profile.research_interests.add(self.ai, self.biology)
        self.researcher_role = JobRole.objects.get(name="Researcher")
        self.profile.preferred_roles.add(self.researcher_role)
        PreferredInstitution.objects.create(
            researcher_profile=self.profile,
            university=self.university,
            priority=1,
        )

    def test_complete_match_scores_weighted_components(self):
        job = self._job(
            title="Artificial Intelligence Researcher",
            description="PhD required for machine learning research.",
            required_degree="PhD",
            employment_type="Full time",
            location="Quito, Ecuador",
        )

        result = MatchService.match(job, self.profile)

        self.assertEqual(result["score"], 91)
        self.assertTrue(result["matched"])
        self.assertEqual(result["missing"], [])
        self.assertIn("Score 91/100", result["explanation"])
        self.assertIn("matched role: Researcher", result["explanation"])

    def test_non_matching_job_returns_zero_and_all_missing_dimensions(self):
        job = self._job(
            university=self.other_university,
            title="Finance Manager",
            description="Bachelor degree required.",
            required_degree="Bachelor's",
            employment_type="Part time",
            location="Guayaquil",
        )

        result = MatchService.match(job, self.profile)

        self.assertEqual(result["score"], 15)
        self.assertFalse(result["matched"])
        self.assertEqual(
            result["missing"],
            [
                "research_interest",
                "position_type",
                "institution_preference",
                "employment_type",
                "location",
            ],
        )

    def test_score_is_capped_to_zero_through_one_hundred(self):
        job = self._job(
            title="Artificial Intelligence Researcher",
            description="PhD required. Biology research.",
            required_degree="PhD",
            keywords=["Artificial Intelligence", "Biology", "Research"],
            employment_type="Full time",
            location="Quito",
        )

        result = MatchService.match(job, self.profile)

        self.assertEqual(result["score"], 100)
        self.assertTrue(result["matched"])

    def test_role_alias_matches_normalized_job_title(self):
        job = self._job(title="Senior Research-Fellow in AI")

        result = MatchService.match(job, self.profile)

        self.assertEqual(result["score"], 40)
        self.assertIn("matched role: Researcher", result["explanation"])

    def test_exact_role_name_matches(self):
        job = self._job(title="Researcher")

        result = MatchService.match(job, self.profile)

        self.assertEqual(result["score"], 40)
        self.assertNotIn("position_type", result["missing"])

    def test_multiple_preferred_roles_match_most_specific_role(self):
        scientist = JobRole.objects.get(name="Research Scientist")
        self.profile.preferred_roles.add(scientist)
        job = self._job(title="Senior Research Scientist")

        result = MatchService.match(job, self.profile)

        self.assertIn("matched role: Research Scientist", result["explanation"])

    def test_inactive_preferred_role_is_ignored(self):
        self.researcher_role.is_active = False
        self.researcher_role.save(update_fields=["is_active"])
        job = self._job(title="Research Fellow")

        result = MatchService.match(job, self.profile)

        self.assertEqual(result["score"], 20)
        self.assertIn("position_type", result["missing"])
        self.assertIn("matched role: none", result["explanation"])

    def _job(self, **overrides):
        values = {
            "university": self.university,
            "source": "test",
            "external_id": f"job-{Job.objects.count() + 1}",
            "title": "Research role",
            "url": "https://example.edu/job",
            "description": "",
            "employment_type": "",
            "location": "",
        }
        values.update(overrides)
        return Job.objects.create(**values)
