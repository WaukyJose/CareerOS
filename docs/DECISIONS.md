# Decisions

This file records significant product and architecture decisions for CareerOS.

## D001 - Django and PostgreSQL as Core Platform

Status: Accepted

CareerOS will be built as a Django application backed by PostgreSQL. Django provides mature administrative tooling, ORM support, migration management, and a clear path for web workflows. PostgreSQL provides reliable relational storage for normalized opportunity data, source metadata, ranking inputs, and tracking history.

## D002 - VS Milestone Methodology

Status: Accepted

CareerOS will progress through iterative VS milestones. Each VS must define objective, scope, deliverables, acceptance criteria, definition of done, and future dependencies. This keeps delivery focused on verifiable vertical slices.

## D003 - Collector Isolation

Status: Accepted

Source-specific collectors will be isolated behind a collector framework. Core institution, opportunity, ranking, and tracking models must not depend directly on a single source implementation.

## D004 - VS001 Development-Only Django Skeleton

Status: Accepted

VS001 initializes a minimal Django project under `backend/` without creating domain apps or models. Settings are development-only and use SQLite temporarily so the project can run locally before PostgreSQL integration is introduced in a later milestone.

## D005 - University Registry Seed Source and Identity

Status: Accepted

VS002 models Ecuadorian universities in a dedicated `universities` Django app. University names are treated as the natural import identity for the seed registry, allowing `import_universities` to be idempotent through update-or-create behavior. The initial CSV seed is based on the Consejo de Educación Superior university categories: public national, private cofinanced, and private self-financed institutions.

## D006 - Collector Framework Without Persistence

Status: Accepted

VS003 introduces a source-agnostic collector framework with `BaseCollector`, `JobRecord`, `CollectorResult`, retry/backoff utilities, logging, and an in-memory registry. The framework intentionally does not scrape websites or persist job records; source-specific collection and job storage will be introduced in later milestones.

## D007 - ESPE Collector Reads Source URL From Registry

Status: Accepted

VS004 introduces `ESPECollector` as the first source-specific collector. The collector reads ESPE's public jobs page from `University.jobs_url` instead of hardcoding the URL in collector logic. It parses public listing links into `JobRecord` objects and does not persist jobs, preserving the VS003 separation between collection and storage.

## D008 - Jobs Are Upserted By Source Identity

Status: Accepted

VS005 persists collector output in a dedicated `jobs` app. Jobs are uniquely identified by `(source, external_id)`, where `external_id` is mapped from `JobRecord.source_id`. `JobService.upsert` creates unseen jobs, skips unchanged jobs, updates modified jobs, and reactivates closed jobs when a changed listing appears again. Collector execution statistics are stored separately from job records.

## D009 - Read-Only Jobs API With DRF

Status: Accepted

VS006 uses Django REST Framework to expose persisted jobs through read-only list and detail endpoints. The API intentionally does not add authentication, frontend behavior, or matching logic. Filtering and ordering are implemented in the `JobViewSet` to keep the first API slice explicit and small.

## D010 - Database-Backed Collector Discovery

Status: Accepted

VS007 moves collector execution from import-time registration to database-backed collector definitions. Each `Collector` row links to a university, stores the module path for dynamic class discovery, and controls enabled state, priority, timeout, run timestamps, and status. `run_collectors` executes enabled collectors in priority order and records configuration or import failures as collector execution errors.

## D011 - Celery Scheduler With Redis Broker

Status: Accepted

VS008 uses Celery with Redis transport to run all enabled collectors automatically at 07:00, 13:00, and 19:00 each day. The scheduled task calls the existing `run_collectors` management command to preserve collector execution behavior. A database-backed scheduler lock prevents overlapping collector runs from executing concurrently.

## D012 - Configurable Generic HTML Collector

Status: Accepted

VS009 adds `GenericHTMLCollector` for universities whose public job pages can be parsed with configured CSS or XPath selectors. Selector configuration is stored on `Collector` rows, allowing new HTML-based sources to be added without writing Python. The collector skips incomplete listings and returns `JobRecord` objects for persistence through the existing collector pipeline.
