from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from common.models import BaseModel


class JobRole(BaseModel):
    class Category(models.TextChoices):
        ACADEMIC = "Academic", "Academic"
        EDUCATION = "Education", "Education"
        RESEARCH = "Research", "Research"
        CONSULTING = "Consulting", "Consulting"
        INDUSTRY = "Industry", "Industry"
        MANAGEMENT = "Management", "Management"

    name = models.CharField(max_length=120, unique=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    aliases = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return self.name


class ResearchInterest(BaseModel):
    name = models.CharField(max_length=120, unique=True)
    weight = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ResearcherProfile(BaseModel):
    user = models.OneToOneField(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="researcher_profile",
    )
    full_name = models.CharField(max_length=255)
    highest_degree = models.CharField(max_length=120, blank=True)
    current_position = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=120, blank=True)
    city = models.CharField(max_length=120, blank=True)
    preferred_employment_types = models.JSONField(default=list, blank=True)
    preferred_locations = models.JSONField(default=list, blank=True)
    minimum_match_score = models.PositiveSmallIntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    is_active = models.BooleanField(default=True)
    research_interests = models.ManyToManyField(
        ResearchInterest,
        related_name="researcher_profiles",
        blank=True,
    )
    preferred_roles = models.ManyToManyField(
        JobRole,
        related_name="researcher_profiles",
        blank=True,
    )

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name


class PreferredInstitution(BaseModel):
    researcher_profile = models.ForeignKey(
        ResearcherProfile,
        on_delete=models.CASCADE,
        related_name="preferred_institutions",
    )
    university = models.ForeignKey(
        "universities.University",
        on_delete=models.CASCADE,
        related_name="preferred_by_researchers",
    )
    priority = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["priority", "university__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["researcher_profile", "university"],
                name="unique_profile_preferred_institution",
            ),
        ]

    def __str__(self):
        return f"{self.researcher_profile}: {self.university}"


class JobMatch(models.Model):
    job = models.ForeignKey(
        "jobs.Job",
        on_delete=models.CASCADE,
        related_name="matches",
    )
    researcher_profile = models.ForeignKey(
        ResearcherProfile,
        on_delete=models.CASCADE,
        related_name="job_matches",
    )
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    matched = models.BooleanField(default=False)
    matched_role = models.ForeignKey(
        JobRole,
        on_delete=models.SET_NULL,
        related_name="job_matches",
        null=True,
        blank=True,
    )
    explanation = models.JSONField(default=dict)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-score", "-computed_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["job", "researcher_profile"],
                name="unique_job_researcher_match",
            ),
        ]
        indexes = [
            models.Index(fields=["researcher_profile", "score"], name="match_profile_score_idx"),
            models.Index(fields=["matched"], name="match_matched_idx"),
            models.Index(fields=["computed_at"], name="match_computed_idx"),
        ]

    def __str__(self):
        return f"{self.researcher_profile} / {self.job}: {self.score}"
