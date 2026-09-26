from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from jobs.views import JobViewSet
from profiles.views import CurrentResearcherProfileView, JobMatchViewSet
from applications.views import ApplicationViewSet
from dashboard.views import (
    DashboardClosingSoonView,
    DashboardRecentJobsView,
    DashboardSummaryView,
    DashboardTopMatchesView,
)


router = DefaultRouter()
router.register("jobs", JobViewSet, basename="job")
router.register("matches", JobMatchViewSet, basename="match")
router.register("applications", ApplicationViewSet, basename="application")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/token/", obtain_auth_token, name="api-token"),
    path("api/profile/", CurrentResearcherProfileView.as_view(), name="current-profile"),
    path("api/dashboard/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("api/dashboard/top-matches/", DashboardTopMatchesView.as_view(), name="dashboard-top-matches"),
    path("api/dashboard/recent/", DashboardRecentJobsView.as_view(), name="dashboard-recent"),
    path("api/dashboard/closing-soon/", DashboardClosingSoonView.as_view(), name="dashboard-closing-soon"),
    path("api/", include(router.urls)),
]
