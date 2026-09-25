# VS009 - Generic HTML Collector

## Objective

Allow simple university job pages to be collected through database configuration instead of source-specific Python code.

## Scope

- Create `GenericHTMLCollector`.
- Add CSS/XPath selector fields to `Collector`.
- Read selectors from database configuration.
- Support relative URLs.
- Normalize whitespace.
- Skip incomplete listings gracefully.
- Add fixture HTML and mocked tests.
- Document no-code university collector setup.

## Deliverables

- `collectors.generic_html.GenericHTMLCollector`.
- Selector fields on `Collector`.
- Migration for selector configuration.
- Generic HTML fixture and tests.
- README and decision-log updates.

## Acceptance Criteria

- Generic collector inherits `BaseCollector`.
- Selector configuration is read from the database.
- CSS and XPath selectors are supported.
- Relative URLs resolve against `University.jobs_url`.
- Missing title or link skips a listing without failing the run.
- Tests pass.

## Definition of Done

- VS009 acceptance criteria are verified.
- Migrations apply successfully.
- Decisions are recorded in `docs/DECISIONS.md`.

## Status

Complete.
