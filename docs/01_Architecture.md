# Architecture

CareerOS is planned as a modular Django application backed by PostgreSQL.

## System Components

- Django web application for user workflows, administration, and API endpoints.
- PostgreSQL database for normalized institutions, opportunities, rankings, and tracking records.
- Collector framework for source-specific job discovery modules.
- Ranking service for scoring opportunities against configurable criteria.
- Background execution layer for scheduled collection and monitoring jobs.

## Architectural Principles

- Keep collectors isolated from core domain logic.
- Store normalized opportunity data separately from raw source data.
- Preserve source URLs, timestamps, and collection metadata for auditability.
- Prefer explicit domain models over loosely structured records.
- Build vertical slices through VS milestones before broadening feature scope.

## Initial Module Boundaries

- `institutions`: university and research organization registry.
- `opportunities`: normalized job and fellowship listings.
- `collectors`: reusable collection contracts and source-specific implementations.
- `ranking`: scoring rules and ranking explanations.
- `tracking`: user opportunity status and application history.

## Operational Assumptions

- PostgreSQL is the source of truth.
- Django migrations will manage schema evolution.
- Scheduled collection will be introduced after the first source-specific collector is proven.
- Observability requirements will grow as automated collection expands.

