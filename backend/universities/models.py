from django.db import models

from common.models import BaseModel


class University(BaseModel):
    class UniversityType(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVATE_COFINANCED = "private_cofinanced", "Private cofinanced"
        PRIVATE_SELFFINANCED = "private_selffinanced", "Private self-financed"

    class RegistryStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        NEEDS_REVIEW = "needs_review", "Needs review"

    name = models.CharField(max_length=255, unique=True)
    city = models.CharField(max_length=120)
    province = models.CharField(max_length=120)
    type = models.CharField(max_length=32, choices=UniversityType.choices)
    website = models.URLField(max_length=255)
    jobs_url = models.URLField(max_length=255, blank=True)
    status = models.CharField(
        max_length=32,
        choices=RegistryStatus.choices,
        default=RegistryStatus.ACTIVE,
    )
    class Meta:
        ordering = ["name"]
        verbose_name_plural = "universities"

    def __str__(self):
        return self.name

# Create your models here.
