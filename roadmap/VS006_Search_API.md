# VS006 - Search API

## Objective

Expose persisted jobs through a read-only API with filtering, search, ordering, and pagination.

## Scope

- Install and configure Django REST Framework.
- Create read-only job list and detail endpoints.
- Support filters for university, province, city, status, source, and text query.
- Support ordering by newest, deadline, and university.
- Add pagination.
- Add serializer and API tests.
- Register API routes.
- Do not add authentication, frontend UI, or matching logic.

## Deliverables

- `JobSerializer`.
- Read-only `JobViewSet`.
- Routes for `GET /api/jobs/` and `GET /api/jobs/<id>/`.
- DRF pagination configuration.
- Serializer and API tests.
- README and decision-log updates.

## Acceptance Criteria

- `GET /api/jobs/` returns paginated job results.
- `GET /api/jobs/<id>/` returns one job.
- Filters work for university, province, city, status, source, and `q`.
- Ordering works for newest, deadline, and university.
- Mutating API methods are not allowed.
- Tests pass.

## Definition of Done

- VS006 acceptance criteria are verified.
- DRF is pinned in `requirements.txt`.
- API routes are registered.
- Decisions are recorded in `docs/DECISIONS.md`.

## Future Dependencies

- Future milestones may add authentication, saved searches, matching, or frontend views.

## Status

Complete.
