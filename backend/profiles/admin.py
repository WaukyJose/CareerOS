from django.contrib import admin

from .models import JobMatch, JobRole, PreferredInstitution, ResearcherProfile, ResearchInterest


class PreferredInstitutionInline(admin.TabularInline):
    model = PreferredInstitution
    extra = 0


@admin.register(ResearcherProfile)
class ResearcherProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "highest_degree", "current_position", "city", "is_active")
    list_filter = ("is_active", "country", "city")
    search_fields = ("full_name", "user__username", "user__email", "highest_degree", "current_position", "country", "city")
    filter_horizontal = ("research_interests", "preferred_roles")
    inlines = (PreferredInstitutionInline,)
    readonly_fields = ("created_at", "updated_at")


@admin.register(ResearchInterest)
class ResearchInterestAdmin(admin.ModelAdmin):
    list_display = ("name", "weight")
    search_fields = ("name",)


@admin.register(PreferredInstitution)
class PreferredInstitutionAdmin(admin.ModelAdmin):
    list_display = ("researcher_profile", "university", "priority")
    list_filter = ("priority", "university")
    search_fields = ("researcher_profile__full_name", "university__name")


@admin.register(JobRole)
class JobRoleAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name",)


@admin.register(JobMatch)
class JobMatchAdmin(admin.ModelAdmin):
    list_display = ("job", "researcher_profile", "score", "matched", "matched_role", "computed_at")
    list_filter = ("matched", "matched_role", "job__university")
    search_fields = (
        "job__title",
        "job__university__name",
        "researcher_profile__full_name",
        "matched_role__name",
    )
    ordering = ("-score", "-computed_at")
    readonly_fields = ("explanation", "computed_at")
