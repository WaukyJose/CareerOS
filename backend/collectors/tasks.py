import logging

from celery import shared_task
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import SchedulerLock


logger = logging.getLogger("collectors.scheduler")


@shared_task(name="collectors.tasks.run_all_collectors")
def run_all_collectors():
    logger.info("Starting scheduled collector run.")
    if not _acquire_lock("run_all_collectors"):
        logger.warning("Scheduled collector run skipped because another run is active.")
        return {"status": "skipped", "reason": "overlap"}

    try:
        call_command("run_collectors")
        logger.info("Scheduled collector run completed.")
        return {"status": "completed"}
    except Exception:
        logger.exception("Scheduled collector run failed.")
        raise
    finally:
        _release_lock("run_all_collectors")


def _acquire_lock(name):
    try:
        with transaction.atomic():
            SchedulerLock.objects.create(name=name, acquired_at=timezone.now())
        return True
    except IntegrityError:
        return False


def _release_lock(name):
    SchedulerLock.objects.filter(name=name).delete()
