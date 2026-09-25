from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from jobs.views import JobViewSet


router = DefaultRouter()
router.register("jobs", JobViewSet, basename="job")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
]
