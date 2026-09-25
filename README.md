# CareerOS

CareerOS is a Django/PostgreSQL application for discovering, monitoring, ranking, and tracking academic and research job opportunities.

The project follows an iterative VS milestone methodology. Each VS defines a bounded vertical slice with clear scope, deliverables, acceptance criteria, definition of done, and future dependencies.

## Documentation

- `docs/00_Project_Vision.md` - product purpose, users, and success criteria.
- `docs/01_Architecture.md` - target system architecture.
- `docs/02_Data_Model.md` - initial domain model.
- `docs/03_Coding_Standards.md` - engineering conventions.
- `docs/DECISIONS.md` - architectural and product decision log.
- `roadmap/` - VS milestone specifications.

## Current Status

VS001 project initialization is complete. The repository contains a minimal development-only Django project in `backend/`. No domain apps, models, production settings, or PostgreSQL integration have been implemented.

## Local Setup

Requirements:

- Python 3.12 or compatible Python 3 version

Create and activate the virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the development server:

```bash
cd backend
python manage.py runserver
```

The VS001 project uses Django's development server and temporary SQLite configuration only. PostgreSQL remains the target database for future milestones.

## University Registry

Apply migrations:

```bash
cd backend
python manage.py migrate
```

Import the Ecuador university registry seed data:

```bash
python manage.py import_universities
```

The importer reads `data/ecuador_universities.csv` by default and is idempotent. Re-running it updates existing universities by name instead of creating duplicates.

Run tests:

```bash
python manage.py test
```

## Collector Framework

VS003 provides source-agnostic collector contracts only. It does not scrape websites, persist job records, or implement source-specific collectors.

Run registered collectors:

```bash
cd backend
python manage.py run_collectors
```

Run the ESPE collector:

```bash
cd backend
python manage.py run_collectors espe
```

The ESPE collector reads its public jobs URL from the `University.jobs_url` field, fetches publicly available listing pages, and returns `JobRecord` objects through the collector framework. VS004 does not create a Job model or save scraped jobs to the database.

## Jobs Persistence

VS005 persists collector output to the `jobs` app through `JobService.upsert`.

Behavior:

- New `(source, external_id)` records create jobs with status `NEW`.
- Unchanged records are ignored and counted as skipped.
- Modified records update the existing job.
- Closed jobs become `ACTIVE` again when a modified listing is seen.
- Each collector run records execution statistics.

Run a collector and persist returned jobs:

```bash
cd backend
python manage.py run_collectors espe
```

## Collector Discovery

VS007 stores collector configuration in the database. Each collector is linked to a university and defines:

- `name`
- `module_path`
- `enabled`
- `priority`
- `timeout`
- `last_run`
- `last_success`
- `status`

Run all enabled collectors in priority order:

```bash
cd backend
python manage.py run_collectors
```

Run one enabled collector by name:

```bash
python manage.py run_collectors espe
```

Disabled collectors are skipped. Invalid module paths are recorded as failed collector executions instead of stopping unrelated collectors.

### Generic HTML Collectors

VS009 allows configuring a new university collector without writing Python. Create a `Collector` row with:

- `module_path`: `collectors.generic_html.GenericHTMLCollector`
- `university`: the target university with `jobs_url` set
- `list_selector`: CSS or XPath selector for each listing
- `title_selector`: selector inside each listing for the title
- `link_selector`: selector inside each listing for the job link
- `date_selector`: optional selector for visible date text
- `description_selector`: optional selector for summary text

CSS selectors are used by default. Selectors beginning with `/` or `.//` are treated as XPath. Relative links are resolved against the university `jobs_url`.

### Extraction Quality

VS010 adds shared extraction filtering for collectors. The framework ignores document files, spreadsheets, presentations, archives, images, viewer/download URLs, and links inside navigation, menu, header, or footer regions. `Collector.include_patterns` and `Collector.exclude_patterns` accept one regular expression per line. `allowed_extensions` and `blocked_extensions` accept comma- or whitespace-separated extensions; the built-in unsafe attachment and image blocklist always applies.

Generic and ESPE collectors use the shared extraction utilities to keep only vacancy-like links, resolve and preserve source URLs, normalize whitespace, remove duplicates, and populate available dates and basic role metadata. A page containing only attachments or non-vacancy links produces zero jobs.

## Scheduler

VS008 makes collector execution autonomous with Celery and Redis.

Start Redis locally:

```bash
redis-server
```

Start a Celery worker:

```bash
cd backend
celery -A config worker -l info
```

Start Celery beat:

```bash
cd backend
celery -A config beat -l info
```

Scheduled collector runs execute every day at:

- 07:00
- 13:00
- 19:00

The scheduled task calls the existing `run_collectors` command and uses a database lock to skip overlapping executions.

## Search API

VS006 exposes a read-only JSON API for persisted jobs.

Endpoints:

- `GET /api/jobs/`
- `GET /api/jobs/<id>/`

Supported filters:

- `university`
- `province`
- `city`
- `status`
- `source`
- `q` for title and description search

Supported ordering:

- `ordering=newest`
- `ordering=deadline`
- `ordering=university`

Responses are paginated. Authentication, frontend UI, and matching are intentionally out of scope for VS006.
