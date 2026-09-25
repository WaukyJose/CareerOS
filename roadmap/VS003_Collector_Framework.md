# VS003 - Collector Framework

## Objective

Define a reusable source-agnostic framework for future academic job opportunity collectors.

## Scope

- Create the `collectors` Django app.
- Define an abstract collector contract.
- Standardize collector output with `JobRecord`.
- Standardize execution summaries with `CollectorResult`.
- Add logging and retry/backoff support.
- Provide an in-memory collector registry.
- Add a no-op `run_collectors` management command.
- Do not scrape websites, create job models, or implement ESPE.

## Deliverables

- `BaseCollector` abstract class.
- `JobRecord` dataclass.
- `CollectorResult` dataclass with new, updated, skipped, and errors counters.
- Retry/backoff utility.
- Collector registry.
- `run_collectors` management command.
- Unit tests for base collector behavior, registry behavior, retry behavior, and runner command.

## Acceptance Criteria

- A future collector can subclass `BaseCollector` and return `JobRecord` instances.
- Collector execution returns `CollectorResult` without requiring job persistence.
- Collector failures are captured as errors and do not crash the runner loop.
- Registry supports future source-specific collectors without changing command code.
- Retry/backoff behavior is covered by tests.
- No website scraping or ESPE collector exists in VS003.

## Definition of Done

- VS003 acceptance criteria are verified.
- Interfaces are source-agnostic.
- Tests pass.
- Decisions are recorded in `docs/DECISIONS.md`.

## Future Dependencies

- VS004 will validate the framework with the ESPE collector.
- Future milestones may add scheduling, retries, and monitoring dashboards.

## Status

Complete.
