# Coding Standards

CareerOS will use consistent Django conventions to keep implementation predictable across VS milestones.

## General Standards

- Favor clear domain names over abbreviations.
- Keep modules aligned with documented architecture boundaries.
- Use Django models and migrations for persistent schema changes.
- Keep business rules in services or domain modules rather than views.
- Prefer explicit validation over implicit assumptions.

## Django Standards

- Keep apps focused on one domain responsibility.
- Use class-based or function-based views consistently within each module.
- Keep admin customization simple and operationally useful.
- Write migrations intentionally and review generated schema changes.
- Avoid cross-app imports that create circular domain dependencies.

## Database Standards

- Use PostgreSQL-compatible field types and constraints.
- Add indexes for lookup paths introduced by accepted VS requirements.
- Preserve source and audit timestamps for collected data.
- Use nullable fields only when the domain state is genuinely optional or unknown.

## Testing Standards

- Add tests for each VS acceptance criterion when implementation begins.
- Prefer focused unit tests for domain rules and integration tests for collector behavior.
- Include regression tests for parsing, normalization, and ranking changes.

## Documentation Standards

- Update roadmap documents when VS scope changes.
- Record significant architectural choices in `docs/DECISIONS.md`.
- Keep documentation concise, current, and tied to implementation decisions.

