from django.db import models
from django.utils import timezone


class Application(models.Model):
    class Status(models.TextChoices):
        SAVED = "SAVED", "Saved"
        APPLIED = "APPLIED", "Applied"
        INTERVIEW = "INTERVIEW", "Interview"
        OFFER = "OFFER", "Offer"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"

    researcher_profile = models.ForeignKey(
        "profiles.ResearcherProfile",
        on_delete=models.CASCADE,
        related_name="applications",
    )
    job = models.ForeignKey(
        "jobs.Job",
        on_delete=models.CASCADE,
        related_name="applications",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SAVED)
    saved_at = models.DateTimeField(default=timezone.now)
    applied_at = models.DateTimeField(null=True, blank=True)
    interview_at = models.DateTimeField(null=True, blank=True)
    offer_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    STATUS_TIMESTAMPS = {
        Status.APPLIED: "applied_at",
        Status.INTERVIEW: "interview_at",
        Status.OFFER: "offer_at",
        Status.ACCEPTED: "accepted_at",
        Status.REJECTED: "rejected_at",
    }

    class Meta:
        ordering = ["-saved_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["researcher_profile", "job"],
                name="unique_researcher_job_application",
            ),
        ]

    def save(self, *args, **kwargs):
        timestamp_field = self.STATUS_TIMESTAMPS.get(self.status)
        if timestamp_field and getattr(self, timestamp_field) is None:
            setattr(self, timestamp_field, timezone.now())
            if kwargs.get("update_fields") is not None:
                kwargs["update_fields"] = set(kwargs["update_fields"]) | {timestamp_field}
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.researcher_profile} / {self.job}: {self.status}"
