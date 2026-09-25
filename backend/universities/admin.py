from django.contrib import admin

from .models import University


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "province", "type", "status", "website", "jobs_url")
    list_filter = ("type", "status", "province")
    search_fields = ("name", "city", "province", "website")
    ordering = ("name",)

# Register your models here.
