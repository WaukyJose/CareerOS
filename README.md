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

VS018 authentication and multi-user isolation are complete. The development application includes university registration, database-backed collectors, enriched job persistence and search, scheduled collection, shared extraction quality controls, Admin-configurable generic HTML collectors, user-owned researcher profiles, weighted job matching, ranked matches, dashboard metrics, and application lifecycle tracking. SQLite remains the local development database; PostgreSQL remains the production target.

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

### No-Code University Configuration

VS011 allows a university to be onboarded through Django Admin:

1. Create the `University` and set its `jobs_url`.
2. Optionally create or select a reusable `Collector template`.
3. Create a `Collector` using `collectors.generic_html.GenericHTMLCollector`.
4. Configure or override the list, title, link, date, and description selectors.
5. Configure optional include/exclude patterns and extension policies.
6. Preview the collector before enabling scheduled runs:

```bash
cd backend
python manage.py test_collector <collector_name>
```

The preview fetches the configured page, prints extracted job titles and source URLs, reports invalid selectors or selectors that match no elements, and does not persist jobs. Generic collector configuration is validated in Admin. Collector health records the latest status, extracted job count, duration, and error message.

### Collector HTTP Robustness

VS011.5 gives each collector a configurable HTTP timeout with a 30-second default. Requests send a CareerOS User-Agent plus HTML `Accept` and Spanish-preferred `Accept-Language` headers. Collection retries are limited to timeouts, connection/URL failures, and transient HTTP responses (`408`, `425`, `429`, and `5xx` gateway/server failures); permanent HTTP responses and extraction errors fail immediately.

Each failed run stores its reason on `CollectorExecution`. A timeout or failure from one source is isolated, so `run_collectors` records the error and continues with the remaining enabled collectors.

### First Configured Universities

VS012 configures USFQ, PUCE, ESPOL, EPN, and UTPL with `GenericHTMLCollector`; no university-specific collector classes are added. Each university uses an official institutional vacancies or academic-concourse page and a database-backed selector template. Configurations can set `deadline_selector` and `max_age_days` in addition to the existing selectors and filters.

The first-university collectors use a 30-day posting preference, discard listings with parsed deadlines before the current date, and exclude closed, finalized, archived, or historical page content. A source with no current vacancies succeeds with zero jobs instead of importing old announcements or attachments. Validation results are recorded in `docs/VS012_VALIDATION.md`.

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

## Researcher Profiles and Matching

VS013 adds `ResearcherProfile`, weighted `ResearchInterest` records, and ranked `PreferredInstitution` records. Profiles store degree, current position, location, employment preferences, preferred locations, an activation flag, and a minimum match threshold. All three models are manageable through Django Admin.

`profiles.services.MatchService.match(job, profile)` returns a score from 0 to 100, a threshold-based `matched` boolean, unmet scoring dimensions in `missing`, and a concise `explanation`. The deterministic score uses these weights:

- Research interests: 35
- Position type: 20
- Degree: 15
- Preferred institution: 10
- Employment type: 10
- Location: 10

Research-interest points are distributed proportionally using each interest's configured weight. VS013 does not add notifications, UI, LLMs, embeddings, or semantic search.

### Job-role taxonomy

VS013.5 adds reusable `JobRole` records grouped into Academic, Education, Research, Consulting, Industry, and Management categories. Each role has normalized aliases and an active flag. A researcher's position preferences are represented by `ResearcherProfile.preferred_roles` instead of free text.

The match service normalizes job titles and compares them with the names and aliases of active preferred roles. The most specific matching preferred role receives the existing 20-point position contribution and is named in the returned explanation. The seed migration creates the initial 29-role taxonomy.

### Persisted and ranked matches

VS014 persists deterministic match results through this pipeline:

```text
Collectors → Jobs → MatchService → JobMatch
```

Run matching for every active job and active researcher profile:

```bash
cd backend
python manage.py compute_matches
```

The command upserts one `JobMatch` for each job/profile pair. Stored results include the score, threshold result, matched role, structured explanation, and computation time.

Ranked matches are available from `GET /api/matches/`. Supported filters are `profile`, `minimum_score`, `matched_only`, and `university`. Use `ordering=score` for highest score first or `ordering=newest` for most recently computed first.

VS014 does not add email, notifications, UI, LLMs, embeddings, or semantic search.

### Deterministic job enrichment

VS015 runs `JobEnrichmentService` when a collected job is first persisted or when its tracked source data changes. Unchanged jobs skip enrichment. The service deterministically extracts and normalizes discipline, department, required degree, employment type, salary, contract type, language, remote status, and keywords.

Examples include normalizing `PhD` and `Doctorado` to `PhD`, and `Tiempo Completo` and `Full Time` to `Full-time`. Unknown values remain blank or preserve collector-provided metadata rather than being guessed. `MatchService` uses normalized degree, discipline, employment type, and keywords.

The matching pipeline is now:

```text
Collectors → JobEnrichmentService → Jobs → MatchService → JobMatch
```

VS015 uses deterministic parsing only and does not use LLMs.

## Dashboard API

VS016 exposes the CareerOS data pipeline through read-only dashboard endpoints:

```text
Collectors → Jobs → Enrichment → Matching → Dashboard
```

Endpoints:

- `GET /api/dashboard/` returns total, active, matched, saved, applied, closing-soon, and recent-job counts plus average and top match scores.
- `GET /api/dashboard/top-matches/` returns the 20 highest-scoring matches, ordered by score descending.
- `GET /api/dashboard/recent/` returns jobs created during the last seven days, newest first.
- `GET /api/dashboard/closing-soon/` returns active jobs due from today through the next 14 days, nearest deadline first.

Dashboard application metrics are cumulative: every application counts as saved, while applied, interview, offer, and accepted totals use their recorded milestone timestamps.

## Application Tracking

VS017 implements this opportunity workflow:

```text
Jobs → Match → Save → Apply → Track
```

Applications are unique per researcher profile and job. Supported statuses are `SAVED`, `APPLIED`, `INTERVIEW`, `OFFER`, `ACCEPTED`, `REJECTED`, and `WITHDRAWN`. Lifecycle transitions preserve milestone timestamps and prevent transitions backward from later or terminal states.

Endpoints:

- `GET /api/applications/`
- `POST /api/applications/`
- `PATCH /api/applications/<id>/`
- `DELETE /api/applications/<id>/`

List filters are `profile`, `status`, and `university`. Use `ordering=newest` for saved time or `ordering=applied_at` for application time, both descending.

VS017 does not add email, notifications, frontend UI, AI, or document generation.

## Authentication

VS018 uses Django users and Django REST Framework token authentication. Every researcher profile belongs to exactly one user. Matches, applications, profile details, personalized dashboard metrics, and dashboard top matches are restricted to that user.

Obtain a token with a Django username and password:

```http
POST /api/token/
Content-Type: application/json

{"username": "ada", "password": "your-password"}
```

Send the returned token on API requests:

```http
Authorization: Token <token>
```

All API endpoints require authentication. `GET` or `PATCH /api/profile/` retrieves or updates only the authenticated user's profile. Attempts to read, update, create, or delete another user's matches or applications are excluded by ownership-scoped querysets and validation.

VS018 does not add a frontend, OAuth, Google login, email, or AI functionality.
