# VS008 - Scheduler

## Objective

Make CareerOS collector execution autonomous by scheduling all enabled collectors to run multiple times per day.

## Scope

- Install Celery.
- Install Redis support.
- Configure Celery for Django.
- Add Celery application wiring and task autodiscovery.
- Create periodic task `run_all_collectors`.
- Schedule runs every day at 07:00, 13:00, and 19:00.
- Call the existing `run_collectors` command from the task.
- Prevent overlapping executions.
- Log task start, completion, skipped overlap, and failure.
- Add tests for task registration and scheduling.
- Do not add email, notifications, or matching.

## Deliverables

- Celery and Redis dependencies.
- `config/celery.py`.
- Celery app export in `config/__init__.py`.
- `collectors.tasks.run_all_collectors`.
- Scheduler lock model and migration.
- Tests for task registration, schedule configuration, command invocation, and overlap prevention.
- README and decision-log updates.

## Acceptance Criteria

- Celery is configured for Django.
- Redis broker/result backend settings exist.
- `run_all_collectors` task is registered.
- Beat schedule contains daily 07:00, 13:00, and 19:00 runs.
- The task calls `run_collectors`.
- Overlapping executions are skipped.
- Tests pass.

## Definition of Done

- VS008 acceptance criteria are verified.
- Migrations apply successfully.
- Decisions are recorded in `docs/DECISIONS.md`.

## Future Dependencies

- Future operational milestones may add deployment process management, monitoring dashboards, notifications, or alerting.

## Status

Complete.
