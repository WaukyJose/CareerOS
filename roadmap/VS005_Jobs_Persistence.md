# VS005 - Jobs Persistence

## Objective

Persist normalized collector output as job records while preserving idempotent collector execution.

## Scope

- Create the `jobs` Django app.
- Add a shared abstract `BaseModel`.
- Migrate `University` to inherit `BaseModel`.
- Create the `Job` model.
- Enforce uniqueness on `(source, external_id)`.
- Add job statuses: `NEW`, `ACTIVE`, and `CLOSED`.
- Link jobs to universities.
- Implement `JobService.upsert(JobRecord)`.
- Persist collector output from `run_collectors`.
- Record collector execution statistics.
- Register jobs in Django admin.
- Add migrations and unit tests.

## Deliverables

- `jobs` app with `Job` model, admin registration, migrations, service layer, and tests.
- Shared abstract `BaseModel`.
- `CollectorExecution` statistics model.
- Updated `run_collectors` command that persists `JobRecord` objects.
- README and decision-log updates.

## Acceptance Criteria

- New collector records create jobs.
- Existing unchanged jobs are skipped.
- Existing modified jobs are updated.
- Duplicate `(source, external_id)` jobs are rejected.
- Collector execution statistics are stored.
- `Job` is available in Django admin.
- Tests pass.

## Definition of Done

- VS005 acceptance criteria are verified.
- Migrations apply successfully.
- No source-specific behavior is added beyond persistence of existing collector output.
- Decisions are recorded in `docs/DECISIONS.md`.

## Future Dependencies

- Future ranking and tracking milestones will depend on persisted jobs.
- Future collector milestones can reuse `JobService.upsert`.

## Status

Complete.
