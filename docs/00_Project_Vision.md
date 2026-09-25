# Project Vision

CareerOS is a Django/PostgreSQL application that helps users discover, monitor, rank, and track academic and research job opportunities.

## Purpose

The system will consolidate opportunities from trusted university and research institution sources, normalize collected data, rank opportunities against user-defined criteria, and support an end-to-end application tracking workflow.

## Target Users

- Researchers seeking academic, postdoctoral, faculty, or research staff roles.
- Graduate students preparing for academic and research job markets.
- Career advisors supporting candidates across multiple institutions.

## Product Goals

- Maintain a registry of universities and research institutions.
- Collect opportunity listings through a reusable collector framework.
- Normalize listings into a searchable PostgreSQL-backed domain model.
- Rank opportunities using transparent criteria.
- Track opportunity status from discovery through application outcome.

## Success Criteria

- Users can identify relevant opportunities faster than manual browsing.
- Collected listings are traceable to source institutions.
- Ranking and tracking workflows are explainable, auditable, and repeatable.
- The architecture supports incremental collectors without destabilizing core workflows.

