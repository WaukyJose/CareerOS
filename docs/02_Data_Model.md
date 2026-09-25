# Data Model

The initial data model focuses on traceable institution records, normalized opportunities, and user-centered tracking.

## Core Entities

### Institution

Represents a university, research center, or academic employer.

Key attributes:

- Name
- Country
- Region or state
- Website URL
- Career or jobs URL
- Source status
- Last reviewed timestamp

### Opportunity

Represents a normalized academic or research job listing.

Key attributes:

- Institution
- Title
- Description
- Department or unit
- Location
- Employment type
- Discipline or field
- Source URL
- Posted date
- Deadline date
- Collection status

### Raw Source Record

Stores source-specific collection output before normalization.

Key attributes:

- Collector name
- Source URL
- Retrieved timestamp
- Raw payload
- Parse status
- Error details

### Ranking Profile

Defines criteria used to rank opportunities.

Key attributes:

- Profile name
- Preferred locations
- Disciplines
- Role types
- Keyword preferences
- Exclusion rules

### Tracked Opportunity

Represents a user's workflow state for an opportunity.

Key attributes:

- Opportunity
- User
- Status
- Priority
- Notes
- Next action date
- Outcome

## Modeling Guidelines

- Normalize fields needed for filtering and ranking.
- Retain raw source records for debugging and audit history.
- Avoid collector-specific fields on core opportunity records unless promoted through a documented decision.

