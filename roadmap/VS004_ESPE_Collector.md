# VS004 - ESPE Collector

## Objective

Implement the first source-specific collector for ESPE academic or research job opportunities.

## Scope

- Create `ESPECollector` inheriting `BaseCollector`.
- Register `ESPECollector` with the collector registry.
- Read ESPE's public jobs URL from the `University` model.
- Parse public ESPE listing links into `JobRecord` objects.
- Add deterministic fixture HTML and mocked HTTP tests.
- Do not create a Job model or save jobs to the database.

## Deliverables

- `ESPECollector`.
- ESPE registry configuration through `University.jobs_url`.
- Fixture HTML for deterministic parsing tests.
- Tests for parsing, graceful missing configuration, fetch failure handling, and `run_collectors espe`.
- README and decision-log updates.

## Acceptance Criteria

- ESPE collector is registered.
- ESPE jobs URL is read from `University.jobs_url`, not hardcoded in collector logic.
- Public listing links are converted to `JobRecord` objects.
- Raw link metadata is retained in `JobRecord.raw_data`.
- Parsing failures and fetch errors are logged and handled gracefully.
- HTTP requests are mocked in tests.
- `run_collectors espe` executes successfully in tests.
- No Job model exists and no jobs are saved to the database.

## Definition of Done

- VS004 acceptance criteria are verified.
- Tests pass.
- Decisions are recorded in `docs/DECISIONS.md`.

## Future Dependencies

- Successful ESPE collection will inform additional institution collectors.
- Ranking and tracking milestones depend on normalized opportunity records from collectors.

## Status

Complete.
