from django.core.exceptions import ValidationError
from django.db import models
from lxml import etree, html

from common.models import BaseModel


class CollectorExecution(BaseModel):
    collector_name = models.CharField(max_length=120)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField()
    new = models.PositiveIntegerField(default=0)
    updated = models.PositiveIntegerField(default=0)
    skipped = models.PositiveIntegerField(default=0)
    errors = models.PositiveIntegerField(default=0)
    error_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.collector_name} at {self.started_at:%Y-%m-%d %H:%M:%S}"


class CollectorTemplate(BaseModel):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    list_selector = models.CharField(max_length=255)
    title_selector = models.CharField(max_length=255)
    link_selector = models.CharField(max_length=255)
    date_selector = models.CharField(max_length=255, blank=True)
    deadline_selector = models.CharField(max_length=255, blank=True)
    description_selector = models.CharField(max_length=255, blank=True)
    include_patterns = models.TextField(blank=True)
    exclude_patterns = models.TextField(blank=True)
    allowed_extensions = models.TextField(blank=True)
    blocked_extensions = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def clean(self):
        _validate_selectors(self)


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
    template = models.ForeignKey(
        CollectorTemplate,
        on_delete=models.SET_NULL,
        related_name="collectors",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=120, unique=True)
    module_path = models.CharField(max_length=255)
    enabled = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=100)
    timeout = models.PositiveIntegerField(default=30)
    list_selector = models.CharField(max_length=255, blank=True)
    title_selector = models.CharField(max_length=255, blank=True)
    link_selector = models.CharField(max_length=255, blank=True)
    date_selector = models.CharField(max_length=255, blank=True)
    deadline_selector = models.CharField(max_length=255, blank=True)
    description_selector = models.CharField(max_length=255, blank=True)
    include_patterns = models.TextField(blank=True)
    exclude_patterns = models.TextField(blank=True)
    allowed_extensions = models.TextField(blank=True)
    blocked_extensions = models.TextField(blank=True)
    max_age_days = models.PositiveIntegerField(null=True, blank=True)
    last_run = models.DateTimeField(null=True, blank=True)
    last_success = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IDLE,
    )

    class HealthStatus(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        HEALTHY = "healthy", "Healthy"
        EMPTY = "empty", "No jobs found"
        ERROR = "error", "Error"

    health_status = models.CharField(
        max_length=20,
        choices=HealthStatus.choices,
        default=HealthStatus.UNKNOWN,
    )
    last_job_count = models.PositiveIntegerField(null=True, blank=True)
    last_duration = models.DurationField(null=True, blank=True)
    last_error = models.TextField(blank=True)

    class Meta:
        ordering = ["priority", "name"]

    def __str__(self):
        return self.name

    def clean(self):
        if self.module_path != "collectors.generic_html.GenericHTMLCollector":
            return
        errors = {}
        if not self.university_id or not self.university.jobs_url:
            errors["university"] = "Generic collectors require a university jobs URL."
        for field in ("list_selector", "title_selector", "link_selector"):
            if not self.config_value(field):
                errors[field] = "This selector is required for a generic HTML collector."
        if not errors:
            try:
                _validate_selectors(self, value_getter=self.config_value)
            except ValidationError as exc:
                errors.update(exc.message_dict)
        if errors:
            raise ValidationError(errors)

    def config_value(self, field):
        value = getattr(self, field, "")
        if value:
            return value
        if self.template_id:
            return getattr(self.template, field, "")
        return ""


class SchedulerLock(BaseModel):
    name = models.CharField(max_length=120, unique=True)
    acquired_at = models.DateTimeField()

    def __str__(self):
        return self.name


def _validate_selectors(instance, value_getter=None):
    value_getter = value_getter or (lambda field: getattr(instance, field, ""))
    errors = {}
    document = html.fromstring("<html><body><div></div></body></html>")
    for field in (
        "list_selector", "title_selector", "link_selector",
        "date_selector", "deadline_selector", "description_selector",
    ):
        selector = value_getter(field)
        if not selector:
            continue
        try:
            if selector.startswith("/") or selector.startswith("./"):
                etree.XPath(selector)
            else:
                document.cssselect(selector)
        except Exception as exc:
            errors[field] = f"Invalid selector: {exc}"
    if errors:
        raise ValidationError(errors)
