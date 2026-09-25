# VS007 - Collector Discovery

## Objective

Move collector execution configuration into the database so collectors can be enabled, disabled, prioritized, and discovered dynamically.

## Scope

- Add `Collector` model.
- Link collectors to universities.
- Store name, module path, enabled flag, priority, timeout, last run, last success, and status.
- Load collector classes from `module_path`.
- Skip disabled collectors.
- Execute enabled collectors ordered by priority.
- Record invalid module paths as failed executions.
- Add admin interface.
- Add tests for discovery, enable/disable, ordering, and invalid module paths.

## Deliverables

- `Collector` model and migrations.
- Seed configuration for the ESPE collector.
- Database-backed collector discovery in the registry.
- Updated `run_collectors` command.
- Admin registration for collector configuration.
- Tests covering VS007 discovery behavior.
- README and decision-log updates.

## Acceptance Criteria

- Enabled collectors are discovered from the database.
- Disabled collectors are skipped.
- Collectors run ordered by priority.
- Collector classes are imported from `module_path`.
- Invalid module paths are handled gracefully and recorded as errors.
- Collector status, last run, and last success are updated.
- Tests pass.

## Definition of Done

- VS007 acceptance criteria are verified.
- Migrations apply successfully.
- Decisions are recorded in `docs/DECISIONS.md`.

## Future Dependencies

- Future scheduler or dashboard milestones can manage collector rows directly.
- Additional source collectors can be added without changing command routing.

## Status

Complete.
