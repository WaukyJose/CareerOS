import os

from celery import Celery
from celery.schedules import crontab


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("career_os")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.beat_schedule.update(
    {
        "run-all-collectors-0700": {
            "task": "collectors.tasks.run_all_collectors",
            "schedule": crontab(hour=7, minute=0),
        },
        "run-all-collectors-1300": {
            "task": "collectors.tasks.run_all_collectors",
            "schedule": crontab(hour=13, minute=0),
        },
        "run-all-collectors-1900": {
            "task": "collectors.tasks.run_all_collectors",
            "schedule": crontab(hour=19, minute=0),
        },
    }
)
app.autodiscover_tasks()
