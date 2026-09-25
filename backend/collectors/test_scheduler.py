from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from collectors.models import SchedulerLock
from collectors.tasks import run_all_collectors
from config.celery import app


class SchedulerTests(TestCase):
    def test_task_is_registered(self):
        self.assertIn("collectors.tasks.run_all_collectors", app.tasks)

    def test_beat_schedule_contains_three_daily_runs(self):
        schedule = app.conf.beat_schedule

        self.assertEqual(
            set(schedule),
            {
                "run-all-collectors-0700",
                "run-all-collectors-1300",
                "run-all-collectors-1900",
            },
        )
        self.assertEqual(
            schedule["run-all-collectors-0700"]["task"],
            "collectors.tasks.run_all_collectors",
        )
        self.assertEqual(schedule["run-all-collectors-0700"]["schedule"]._orig_hour, 7)
        self.assertEqual(schedule["run-all-collectors-1300"]["schedule"]._orig_hour, 13)
        self.assertEqual(schedule["run-all-collectors-1900"]["schedule"]._orig_hour, 19)
        self.assertEqual(schedule["run-all-collectors-0700"]["schedule"]._orig_minute, 0)

    @patch("collectors.tasks.call_command")
    def test_task_calls_run_collectors_command(self, call_command):
        result = run_all_collectors()

        call_command.assert_called_once_with("run_collectors")
        self.assertEqual(result, {"status": "completed"})
        self.assertFalse(SchedulerLock.objects.exists())

    @patch("collectors.tasks.call_command")
    def test_task_skips_when_lock_exists(self, call_command):
        SchedulerLock.objects.create(
            name="run_all_collectors",
            acquired_at=timezone.now(),
        )

        result = run_all_collectors()

        call_command.assert_not_called()
        self.assertEqual(result, {"status": "skipped", "reason": "overlap"})
