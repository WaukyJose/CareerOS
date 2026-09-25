# VS010 - Extraction Quality

## Objective

Improve extraction quality while keeping the collector framework generic.

## Scope

- Add link filtering utilities.
- Ignore documents, spreadsheets, presentations, archives, images, viewer links, download links, and navigation/menu links.
- Add configurable include/exclude patterns.
- Add shared `JobExtractor` utility.
- Refactor ESPE collector to use `JobExtractor`.
- Extract only vacancy records.
- Populate available title, department, discipline, employment type, posted date, and deadline date.
- Preserve source URLs.
- Update fixtures and regression tests.

## Deliverables

- `collectors.extraction.JobExtractor`.
- `collectors.extraction.LinkFilter`.
- Include/exclude pattern fields on `Collector`.
- ESPE extractor refactor.
- Updated ESPE fixture with vacancy and non-vacancy links.
- Regression tests.

## Acceptance Criteria

- Non-vacancy file/download/navigation links are ignored.
- Include/exclude patterns are configurable.
- ESPE sample returns only genuine vacancies.
- Relative and absolute source URLs are preserved.
- Missing fields are skipped gracefully.
- Tests pass.

## Definition of Done

- VS010 acceptance criteria are verified.
- Decisions are recorded in `docs/DECISIONS.md`.

## Status

Complete.
