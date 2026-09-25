from django.contrib import admin

from .models import Collector, CollectorExecution


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
        "last_run",
        "last_success",
    )
    list_filter = ("enabled", "status", "university")
    search_fields = ("name", "module_path", "university__name")
    ordering = ("priority", "name")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "university",
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
                    "description_selector",
                    "include_patterns",
                    "exclude_patterns",
                    "allowed_extensions",
                    "blocked_extensions",
                )
            },
        ),
        (
            "Run history",
            {
                "fields": ("last_run", "last_success", "created_at", "updated_at"),
            },
        ),
    )
    readonly_fields = ("created_at", "updated_at", "last_run", "last_success")


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
        "created_at",
        "updated_at",
    )

# Register your models here.
