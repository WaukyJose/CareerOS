from django.contrib import admin

from .models import Collector, CollectorExecution, CollectorTemplate


@admin.register(CollectorTemplate)
class CollectorTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "updated_at")
    search_fields = ("name", "description")


@admin.register(Collector)
class CollectorAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "university",
        "module_path",
        "enabled",
        "priority",
        "timeout",
        "list_selector",
        "status",
        "health_status",
        "last_job_count",
        "last_duration",
        "last_run",
        "last_success",
    )
    list_filter = ("enabled", "status", "health_status", "university")
    search_fields = ("name", "module_path", "university__name")
    ordering = ("priority", "name")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "university",
                    "template",
                    "name",
                    "module_path",
                    "enabled",
                    "priority",
                    "timeout",
                    "status",
                )
            },
        ),
        (
            "HTML selectors",
            {
                "fields": (
                    "list_selector",
                    "title_selector",
                    "link_selector",
                    "date_selector",
                    "deadline_selector",
                    "description_selector",
                    "include_patterns",
                    "exclude_patterns",
                    "allowed_extensions",
                    "blocked_extensions",
                    "max_age_days",
                )
            },
        ),
        (
            "Health and run history",
            {
                "fields": (
                    "health_status", "last_job_count", "last_duration", "last_error",
                    "last_run", "last_success", "created_at", "updated_at",
                ),
            },
        ),
    )
    readonly_fields = (
        "created_at", "updated_at", "last_run", "last_success", "health_status",
        "last_job_count", "last_duration", "last_error",
    )


@admin.register(CollectorExecution)
class CollectorExecutionAdmin(admin.ModelAdmin):
    list_display = (
        "collector_name",
        "started_at",
        "finished_at",
        "new",
        "updated",
        "skipped",
        "errors",
        "error_reason",
    )
    list_filter = ("collector_name",)
    readonly_fields = (
        "collector_name",
        "started_at",
        "finished_at",
        "new",
        "updated",
        "skipped",
        "errors",
        "error_reason",
        "created_at",
        "updated_at",
    )

# Register your models here.
