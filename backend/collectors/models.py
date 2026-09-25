from django.db import models

from common.models import BaseModel


class CollectorExecution(BaseModel):
    collector_name = models.CharField(max_length=120)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField()
    new = models.PositiveIntegerField(default=0)
    updated = models.PositiveIntegerField(default=0)
    skipped = models.PositiveIntegerField(default=0)
    errors = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.collector_name} at {self.started_at:%Y-%m-%d %H:%M:%S}"


class Collector(BaseModel):
    class Status(models.TextChoices):
        IDLE = "idle", "Idle"
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        ERROR = "error", "Error"

    university = models.ForeignKey(
        "universities.University",
        on_delete=models.PROTECT,
        related_name="collectors",
    )
    name = models.CharField(max_length=120, unique=True)
    module_path = models.CharField(max_length=255)
    enabled = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=100)
    timeout = models.PositiveIntegerField(default=20)
    list_selector = models.CharField(max_length=255, blank=True)
    title_selector = models.CharField(max_length=255, blank=True)
    link_selector = models.CharField(max_length=255, blank=True)
    date_selector = models.CharField(max_length=255, blank=True)
    description_selector = models.CharField(max_length=255, blank=True)
    last_run = models.DateTimeField(null=True, blank=True)
    last_success = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IDLE,
    )

    class Meta:
        ordering = ["priority", "name"]

    def __str__(self):
        return self.name


class SchedulerLock(BaseModel):
    name = models.CharField(max_length=120, unique=True)
    acquired_at = models.DateTimeField()

    def __str__(self):
        return self.name
