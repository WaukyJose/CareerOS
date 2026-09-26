from django.core.management.base import BaseCommand

from jobs.models import Job
from profiles.models import JobMatch, ResearcherProfile
from profiles.services import MatchService


class Command(BaseCommand):
    help = "Compute and persist matches for every active job and researcher profile."

    def handle(self, *args, **options):
        jobs = Job.objects.filter(status=Job.Status.ACTIVE).select_related("university")
        profiles = ResearcherProfile.objects.filter(is_active=True).prefetch_related(
            "research_interests",
            "preferred_roles",
            "preferred_institutions",
        )
        created = 0
        updated = 0

        for job in jobs.iterator():
            for profile in profiles:
                result = MatchService.match(job, profile)
                _, was_created = JobMatch.objects.update_or_create(
                    job=job,
                    researcher_profile=profile,
                    defaults={
                        "score": result["score"],
                        "matched": result["matched"],
                        "matched_role": result["matched_role"],
                        "explanation": {
                            "missing": result["missing"],
                            "summary": result["explanation"],
                        },
                    },
                )
                created += int(was_created)
                updated += int(not was_created)

        self.stdout.write(self.style.SUCCESS(f"Matches computed: created={created} updated={updated}"))
