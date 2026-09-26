from django.contrib import admin

from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("researcher_profile", "job", "status", "saved_at", "applied_at")
    list_filter = ("status", "job__university")
    search_fields = (
        "researcher_profile__full_name",
        "job__title",
        "job__university__name",
        "notes",
    )
    ordering = ("-saved_at",)
    readonly_fields = (
        "saved_at",
        "applied_at",
        "interview_at",
        "offer_at",
        "accepted_at",
        "rejected_at",
    )
