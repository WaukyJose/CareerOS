# VS011 - No-Code University Configuration

## Objective

Enable new universities entirely from the database or Django Admin using `GenericHTMLCollector`.

## Scope

- Add reusable collector templates.
- Validate generic selector configuration.
- Add a non-persisting collector preview command.
- Track collector health, job count, duration, and latest error.
- Improve collector lifecycle logging.
- Add regression tests and documentation.

## Deliverables

- `CollectorTemplate` model and Admin interface.
- Template-aware `Collector` configuration.
- `test_collector` management command.
- Collector health fields and run updates.
- Configuration, command, health, and ESPE regression tests.

## Acceptance Criteria

- A generic university collector can be configured without Python changes.
- `python manage.py test_collector <collector_name>` previews extracted jobs.
- Invalid and unmatched selectors are reported.
- Collector health metrics are recorded.
- Existing ESPE behavior and the full test suite pass.

## Definition of Done

- VS011 acceptance criteria are verified.
- README and architectural decisions are updated.

## Status

Complete.
