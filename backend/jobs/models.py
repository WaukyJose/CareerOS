from django.db import models

from common.models import BaseModel


class Job(BaseModel):
    class Status(models.TextChoices):
        NEW = "new", "New"
        ACTIVE = "active", "Active"
        CLOSED = "closed", "Closed"

    university = models.ForeignKey(
        "universities.University",
        on_delete=models.PROTECT,
        related_name="jobs",
    )
    source = models.CharField(max_length=80)
    external_id = models.CharField(max_length=500)
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=1000)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )
    location = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=255, blank=True)
    employment_type = models.CharField(max_length=120, blank=True)
    discipline = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    posted_date = models.DateField(null=True, blank=True)
    deadline_date = models.DateField(null=True, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["title"]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "external_id"],
                name="unique_job_source_external_id",
            ),
        ]

    def __str__(self):
        return self.title

# Create your models here.
