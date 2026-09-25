# VS002 - University Registry

## Objective

Create the foundation for managing Ecuadorian universities that may publish academic or research job opportunities.

## Scope

- Create the `universities` Django app.
- Define and migrate the `University` model.
- Register universities in Django admin.
- Seed all Ecuadorian universities from CSV data.
- Provide an idempotent CSV import command.
- Add focused tests for model behavior and import idempotency.

## Deliverables

- `University` model with location, type, website, status, and timestamps.
- Django admin registration for registry management.
- Migration for the registry schema.
- `import_universities` management command.
- `data/ecuador_universities.csv` seed file.
- Unit tests for model defaults, string representation, and CSV import behavior.

## Acceptance Criteria

- `universities` app exists and is installed.
- University records represent Ecuadorian universities with name, city, province, type, website, and status.
- Registry status supports active, inactive, and needs-review states.
- Admin users can manage universities through Django admin.
- CSV import is idempotent and does not duplicate records by name.
- Migration applies successfully.
- Tests pass.

## Definition of Done

- VS002 acceptance criteria are verified.
- Ecuador university seed data imports successfully.
- Model and import command tests pass.
- Decisions are recorded in `docs/DECISIONS.md`.

## Future Dependencies

- VS003 depends on registry records as collector inputs.
- VS004 depends on registry support for ESPE source metadata.

## Status

Complete.
