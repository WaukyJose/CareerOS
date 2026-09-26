# VS012 - First Universities

## Objective

Enable the first five universities through database configuration and `GenericHTMLCollector`.

## Scope

- Configure official opportunity pages for USFQ, PUCE, ESPOL, EPN, and UTPL.
- Create reusable selector templates and collector definitions.
- Keep only active opportunities and reject expired or historical announcements.
- Prefer postings from the previous 30 days.
- Preserve available posting and deadline dates.
- Validate each source with `test_collector`.

## Deliverables

- University `jobs_url` values and five generic collector definitions.
- Source-specific database templates.
- Configurable deadline selector and maximum posting age.
- Regression tests, validation summary, README, and decision-log updates.

## Acceptance Criteria

- All five targets are configured without source-specific collector classes.
- Expired and older configured listings are excluded.
- Available posting and deadline dates are stored.
- Every collector is validated with `test_collector`.
- All tests pass.

## Status

Complete.
