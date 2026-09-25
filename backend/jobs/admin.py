from django.contrib import admin

from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "university", "source", "status", "updated_at")
    list_filter = ("source", "status", "university")
    search_fields = ("title", "university__name", "source", "external_id", "url")
    readonly_fields = ("created_at", "updated_at")

# Register your models here.
