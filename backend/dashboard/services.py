from datetime import timedelta

from django.db.models import Avg, Max
from django.utils import timezone

from applications.models import Application
from jobs.models import Job
from profiles.models import JobMatch


class DashboardService:
    RECENT_DAYS = 7
    CLOSING_SOON_DAYS = 14
    DEFAULT_TOP_MATCHES = 20

    @classmethod
    def summary(cls, user=None):
        now = timezone.now()
        matches = JobMatch.objects.all()
        applications = Application.objects.all()
        if user is not None:
            matches = matches.filter(researcher_profile__user=user)
            applications = applications.filter(researcher_profile__user=user)
        match_statistics = matches.aggregate(
            average=Avg("score"),
            top=Max("score"),
        )
        return {
            "total_jobs": Job.objects.count(),
            "active_jobs": Job.objects.filter(status=Job.Status.ACTIVE).count(),
            "matched_jobs": matches.filter(matched=True).values("job_id").distinct().count(),
            "saved_jobs": applications.count(),
            "applied_jobs": applications.filter(applied_at__isnull=False).count(),
            "interviews": applications.filter(interview_at__isnull=False).count(),
            "offers": applications.filter(offer_at__isnull=False).count(),
            "accepted": applications.filter(accepted_at__isnull=False).count(),
            "closing_soon": cls.closing_soon().count(),
            "new_jobs_last_7_days": Job.objects.filter(
                created_at__gte=now - timedelta(days=cls.RECENT_DAYS)
            ).count(),
            "average_match_score": round(match_statistics["average"] or 0, 2),
            "top_match_score": match_statistics["top"] or 0,
        }

    @classmethod
    def top_matches(cls, limit=None, user=None):
        limit = limit or cls.DEFAULT_TOP_MATCHES
        queryset = JobMatch.objects.select_related(
            "job__university",
            "researcher_profile",
            "matched_role",
        )
        if user is not None:
            queryset = queryset.filter(researcher_profile__user=user)
        return queryset.order_by("-score", "-computed_at", "-id")[:limit]

    @classmethod
    def recent_jobs(cls):
        cutoff = timezone.now() - timedelta(days=cls.RECENT_DAYS)
        return Job.objects.select_related("university").filter(
            created_at__gte=cutoff
        ).order_by("-created_at", "-id")

    @classmethod
    def closing_soon(cls):
        today = timezone.localdate()
        return Job.objects.select_related("university").filter(
            status=Job.Status.ACTIVE,
            deadline_date__gte=today,
            deadline_date__lte=today + timedelta(days=cls.CLOSING_SOON_DAYS),
        ).order_by("deadline_date", "title", "id")
