from dataclasses import dataclass

from django.core.exceptions import ObjectDoesNotExist

from collectors.types import JobRecord
from universities.models import University

from .models import Job
from .enrichment import JobEnrichmentService


@dataclass(frozen=True)
class JobUpsertResult:
    job: Job
    created: bool = False
    updated: bool = False
    skipped: bool = False


class JobService:
    tracked_fields = (
        "university",
        "title",
        "url",
        "location",
        "department",
        "employment_type",
        "discipline",
        "description",
        "posted_date",
        "deadline_date",
        "raw_data",
    )

    @classmethod
    def upsert(cls, record: JobRecord):
        university = cls._get_university(record)
        defaults = cls._defaults(record, university)

        try:
            job = Job.objects.get(source=record.source, external_id=record.source_id)
        except ObjectDoesNotExist:
            job = Job(
                source=record.source,
                external_id=record.source_id,
                status=Job.Status.NEW,
                **defaults,
            )
            for field, value in JobEnrichmentService.enrich(job).items():
                setattr(job, field, value)
            job.save()
            return JobUpsertResult(job=job, created=True)

        changed = False
        for field, value in defaults.items():
            if getattr(job, field) != value:
                setattr(job, field, value)
                changed = True

        if not changed:
            return JobUpsertResult(job=job, skipped=True)

        if job.status == Job.Status.CLOSED:
            job.status = Job.Status.ACTIVE
        enrichment = JobEnrichmentService.enrich(job)
        for field, value in enrichment.items():
            setattr(job, field, value)
        job.save(update_fields=[*defaults.keys(), *enrichment.keys(), "status", "updated_at"])
        return JobUpsertResult(job=job, updated=True)

    @classmethod
    def _get_university(cls, record):
        return University.objects.get(name=record.institution_name)

    @classmethod
    def _defaults(cls, record, university):
        return {
            "university": university,
            "title": record.title,
            "url": record.source_url,
            "location": record.location,
            "department": record.department,
            "employment_type": record.employment_type,
            "discipline": record.discipline,
            "description": record.description,
            "posted_date": record.posted_date,
            "deadline_date": record.deadline_date,
            "raw_data": record.raw_data,
        }
