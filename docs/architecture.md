# Liquidity Monitor Architecture

## 1. Purpose

This document defines how Liquidity Monitor collects, validates, stores, analyzes, explains, and publishes information about U.S. cash-market liquidity.

The architecture translates the business concepts defined in `domain-model.md` into a practical system design.

The platform is designed around one central principle:

> Each layer should have one clear responsibility, produce an inspectable output, and remain independently testable and rerunnable.

The system must preserve a clear distinction among:

1. Externally published data
2. Validated raw observations
3. Internally calculated metrics
4. Rule-based signals
5. Liquidity assessments
6. Narrative commentary
7. Website presentation

---

# 2. System Overview

The primary analytical flow is:

```text
Official Data Sources
        ↓
Collectors
        ↓
Validation and Normalization
        ↓
Persistent Storage
        ↓
Metric Engine
        ↓
Signal Engine
        ↓
Assessment Engine
        ↓
Commentary Engine
        ↓
Application API
        ↓
Website Frontend
```

Events and Concepts provide context throughout the process.

```text
                    Events
                       ↓
Observations → Metrics → Signals → Assessments → Commentary

                    Concepts
                       ↓
            Explanations and Education
```

The website does not independently calculate liquidity conditions. It displays structured outputs produced by the analytical system.

---

# 3. Architectural Principles

## 3.1 Single Responsibility

Each layer should perform one primary function.

Examples:

* Collectors retrieve data.
* Validators assess data quality.
* The Metric Engine calculates.
* The Signal Engine detects noteworthy conditions.
* The Assessment Engine evaluates liquidity.
* The Commentary Engine explains.
* The API serves information.
* The frontend presents information.

Business logic should not be duplicated across layers.

---

## 3.2 Deterministic Analysis Before AI

All facts, calculations, signals, scores, condition labels, and confidence measures must be produced through deterministic logic.

Generative AI may explain structured analytical outputs, but it must not independently:

* Create observations
* Fill missing data
* Calculate metrics
* Trigger signals
* Assign scores
* Change condition labels
* Override data-quality warnings

The platform must remain analytically functional if the AI service is unavailable.

---

## 3.3 Inspectable Outputs

Every layer must produce outputs that can be reviewed independently.

Examples include:

* Collector responses
* Validated observations
* Metric results
* Triggered signals
* Component scores
* Overall assessments
* Commentary evidence
* Publication records

No important conclusion should depend on hidden intermediate state.

---

## 3.4 Reproducibility

The system should be able to reproduce an Assessment using:

* The applicable observations
* Metric definitions and versions
* Signal definitions and versions
* Event information
* Assessment methodology version
* Data cutoff time

Historical results should not silently change merely because a calculation methodology is later updated.

---

## 3.5 Graceful Degradation

A failure in one source or analytical component should not necessarily prevent the entire platform from operating.

Where reasonable, the system should:

* Preserve the prior published Assessment
* Mark affected data as stale or unavailable
* Recalculate unaffected components
* Reduce confidence
* Publish a clear data-quality notice

The system should not silently replace missing information.

---

## 3.6 Primary Sources First

Official primary publishers should be used whenever practical.

Secondary sources may be used for:

* Backup retrieval
* Cross-checking
* Historical convenience
* Data not readily available from the primary source

The source hierarchy must remain visible in the metadata.

---

## 3.7 Progressive Disclosure

The user interface should support different levels of depth.

A senior decision-maker should be able to understand the headline Assessment quickly.

An analyst should be able to drill down through:

```text
Overall Assessment
        ↓
Component Assessment
        ↓
Signal
        ↓
Metric
        ↓
Observation
        ↓
Data Source
```

Every important number should ultimately be traceable to its supporting evidence.

---

# 4. Major System Layers

## 4.1 Data Sources

### Purpose

External Data Sources provide the official or authoritative information used by Liquidity Monitor.

Initial sources include:

* Federal Reserve Bank of New York
* Board of Governors of the Federal Reserve System
* U.S. Department of the Treasury
* Federal Reserve Economic Data
* Depository Trust & Clearing Corporation, when added later

### Responsibilities

Data Sources are external to the application. The platform records:

* Source identity
* Publication schedule
* Endpoint or retrieval method
* Time zone
* Expected release behavior
* Primary or secondary status

### Constraints

The system must not assume that every source:

* Publishes daily
* Publishes at the same time
* Uses the same date format
* Provides revision history
* Remains continuously available
* Uses consistent units

Source-specific behavior should be handled in the Collector layer.

---

## 4.2 Collector Layer

### Purpose

Collectors retrieve externally published data and convert source-specific responses into a preliminary internal structure.

Each Collector is associated with a specific source or source family.

Examples:

* New York Fed reference-rate collector
* Federal Reserve H.4.1 collector
* Treasury fiscal-data collector
* FRED collector

### Responsibilities

Collectors may:

* Send API or HTTP requests
* Authenticate when required
* Handle source-specific URLs and parameters
* Parse source-specific response formats
* Capture retrieval timestamps
* Apply network timeouts
* Retry appropriate transient failures
* Return structured candidate observations
* Record source response metadata

### Collectors Must Not

Collectors must not:

* Calculate z-scores
* Calculate spreads
* Assign liquidity conditions
* Generate signals
* Write market commentary
* Infer missing observations
* Modify unrelated data

### Output

A Collector returns candidate observations and retrieval metadata.

Example:

```text
Indicator: SOFR
Observation date: 2026-08-04
Value: 4.31
Units: percent
Retrieved at: 2026-08-05 08:04 ET
Source: Federal Reserve Bank of New York
```

### Design Pattern

Collectors should implement a common interface where practical.

Conceptually:

```python
collect() -> CollectionResult
```

A `CollectionResult` should indicate:

* Whether retrieval succeeded
* Which source was queried
* Which indicator or indicators were requested
* How many records were returned
* Retrieval timestamp
* Candidate observations
* Warnings
* Errors

---

## 4.3 Validation and Normalization Layer

### Purpose

The Validation layer determines whether collected data are structurally valid, internally consistent, and suitable for storage and downstream analysis.

Normalization converts source-specific representations into common internal formats without changing economic meaning.

### Responsibilities

Validation may include:

* Required-field checks
* Date parsing
* Numeric conversion
* Unit verification
* Duplicate detection
* Missing-value detection
* Range checks
* Ordering checks
* Unexpected revision detection
* Publication-delay checks
* Staleness checks
* Cross-source comparison, when available

Normalization may include:

* Common date formats
* Common timestamps
* Decimal representation
* Standard indicator identifiers
* Standard units
* Standard source identifiers

### Validation Statuses

Initial statuses may include:

* Valid
* Valid with warning
* Stale
* Missing
* Rejected
* Revised
* Pending review

### Rules

* Raw source values should be retained where practical.
* Invalid observations must not proceed silently.
* Normalization must not change the economic meaning of the data.
* Adjustments and transformations belong in the Metric Engine.
* Warnings should remain attached to the affected observation.

### Output

Validated Observation objects and a validation report.

---

## 4.4 Persistent Storage Layer

### Purpose

Persistent Storage maintains the historical and operational record of the platform.

The initial production database is expected to be PostgreSQL, likely hosted through Google Cloud SQL once the application moves beyond the initial local prototype.

### Data Stored

The database will eventually store:

* Data Sources
* Categories
* Indicators
* Observations
* Observation revisions
* Metrics
* Metric results
* Events
* Signals
* Component Assessments
* Overall Assessments
* Commentary
* Concepts
* Collection runs
* Validation results
* Publication records
* Methodology versions

### Storage Principles

* Raw observations and calculated results should be separated.
* Observation date, publication time, and retrieval time should remain distinct.
* Historical Assessments should remain reproducible.
* Methodology versions should be retained.
* Revisions should be auditable.
* Database writes should be idempotent where practical.

### Idempotency

Running the same Collector twice for the same source record should not create uncontrolled duplicates.

The system should identify records using stable business keys such as:

```text
Indicator
Observation date
Source
Revision or vintage
```

### Initial Development Approach

Version 1 may begin with:

* In-memory objects
* JSON fixtures
* SQLite for local development

PostgreSQL should be introduced before automated historical ingestion and production scoring become central.

---

## 4.5 Metric Engine

### Purpose

The Metric Engine transforms validated observations into reproducible analytical measures.

### Responsibilities

The Metric Engine may calculate:

* Daily changes
* Weekly changes
* Basis-point spreads
* Rolling averages
* Rolling volatility
* Rolling z-scores
* Historical percentiles
* Persistence measures
* Composite measures
* Category-level inputs

### Metric Examples

* SOFR minus EFFR
* SOFR minus IORB
* EFFR minus IORB
* Weekly change in reserve balances
* Four-week change in the TGA
* SOFR 52-week percentile
* Number of consecutive days SOFR exceeds EFFR

### Inputs

Metrics may use:

* Validated Observations
* Other validated Metrics
* Event context
* Defined lookback windows
* Methodology parameters

### Outputs

A Metric result should include:

* Metric identifier
* Effective date
* Value
* Units
* Inputs used
* Data cutoff
* Calculation version
* Validation status
* Warnings

### Metric Engine Must Not

The Metric Engine must not:

* Retrieve external data
* Generate narrative commentary
* Assign overall liquidity scores
* Infer market causes
* Conceal missing inputs

### Rerunning Metrics

Metric calculations should be rerunnable for:

* A single date
* A date range
* A single Metric
* All Metrics affected by a revised Observation

---

## 4.6 Event Engine

### Purpose

The Event Engine maintains scheduled and observed events that may affect liquidity conditions or their interpretation.

### Responsibilities

The Event Engine may:

* Load known calendar events
* Identify month-end and quarter-end
* Track Treasury auction and settlement dates
* Track tax dates
* Track FOMC meetings
* Record extraordinary market events
* Associate Events with affected Categories
* Determine whether an Event is active, upcoming, or completed

### Event Output

An Event record should include:

* Event type
* Date and time
* Expected liquidity relevance
* Affected Categories
* Source
* Status
* Whether the event is scheduled or observed

### Constraints

Events provide context but do not automatically determine a Signal or Assessment.

For example, quarter-end may explain a temporary rate move, but it should not automatically cause the system to label conditions as Normal.

---

## 4.7 Signal Engine

### Purpose

The Signal Engine applies documented rules to Indicators, Metrics, and Events to identify noteworthy market conditions.

### Responsibilities

The Signal Engine may detect:

* Threshold crossings
* Historical extremes
* Persistent divergences
* Accelerating trends
* Conflicting Indicators
* Facility usage
* Calendar-related pressure
* Data-quality concerns
* Structural changes

### Example Signals

* SOFR has exceeded EFFR for five consecutive sessions.
* Reserve balances are at a two-year low.
* SOFR volume is above its 95th historical percentile.
* The TGA increased by more than $75 billion over one week.
* SRF usage became positive.
* Funding Metrics remain stable while reserve Metrics are deteriorating.

### Signal Output

A triggered Signal should include:

* Signal identifier
* Effective date
* Category
* Severity
* Direction
* Confidence or certainty
* Supporting evidence
* Triggering rule version
* Whether the Signal is new, ongoing, or resolved
* Relevant Event context

### Signal Engine Must Not

The Signal Engine must not:

* Generate unsupported narratives
* Hide conflicting Signals
* Assign final component scores by itself
* Allow AI to decide whether a rule triggered

### Signal Persistence

Signals should support:

* First triggered date
* Current duration
* Peak severity
* Resolution date
* Recurrence history

---

## 4.8 Assessment Engine

### Purpose

The Assessment Engine produces the platform's central analytical output: a time-specific evaluation of liquidity conditions.

### Responsibilities

The Assessment Engine combines:

* Metric results
* Active Signals
* Event context
* Data-quality information
* Prior Assessments
* Component methodologies

It produces:

* Component scores
* Component condition labels
* Overall score
* Overall condition label
* Change from prior Assessment
* Confidence
* Positive contributors
* Negative contributors
* Nuances
* Conflicting evidence
* Items to monitor next

### Initial Components

* Funding
* Reserves
* Treasury
* Collateral
* Credit

Some components may initially be marked unavailable or provisional until sufficient Indicators and methodology are implemented.

### Score Philosophy

The score provides rapid orientation.

The supporting detail preserves nuance.

Example:

```text
Overall Score: 78 — Normal

Funding:     91 — Healthy
Reserves:    54 — Tightening
Treasury:    77 — Normal
Collateral:  86 — Healthy
Credit:      82 — Healthy
```

The Assessment must explicitly note that reserve conditions are weaker than the headline score suggests.

### Confidence

Assessment confidence should reflect:

* Data freshness
* Data completeness
* Agreement among Signals
* Breadth of supporting Indicators
* Methodology maturity
* Historical comparability

Confidence does not describe confidence in the publisher's official figure. It describes confidence in the platform's interpretation.

### Assessment Engine Must Not

The Assessment Engine must not:

* Retrieve source data
* Invent missing inputs
* Generate unrestricted prose
* Allow the frontend to modify scores
* Allow AI to override deterministic outputs

### Rerunning Assessments

Assessments should be rerunnable when:

* New data arrive
* Existing data are revised
* Events are updated
* Metric or Signal methodology changes
* A prior run failed

Historical Assessments should retain their original methodology version unless explicitly recomputed and stored as a separate version.

---

## 4.9 Commentary Engine

### Purpose

The Commentary Engine converts structured analytical results into clear written explanations.

### Responsibilities

The Commentary Engine may produce:

* Morning Briefs
* Category summaries
* Indicator commentary
* Signal explanations
* Historical comparisons
* Data-quality notices

### Inputs

Commentary may use only approved structured inputs, such as:

* Current Assessment
* Component Assessments
* Triggered Signals
* Material Metrics
* Relevant Events
* Data-quality warnings
* Approved Concept content
* Prior Assessment changes

### Output Requirements

Commentary should explain:

1. What changed
2. Why it may matter
3. Which Indicators agree or conflict
4. How unusual conditions are
5. What should be monitored next
6. What remains uncertain

### Guardrails

Commentary must:

* Distinguish fact from interpretation
* Avoid unsupported causal claims
* Avoid invented market sentiment
* Avoid investment recommendations
* Mention material stale or missing data
* Preserve conflicting evidence
* Cite the structured evidence supporting important statements

### AI Failure

If the AI service fails:

* The Assessment remains available.
* Component scores remain available.
* Signals remain available.
* A deterministic summary template may be used.
* The site should disclose that extended commentary is temporarily unavailable.

---

## 4.10 Application API

### Purpose

The API provides structured access to the platform's validated and analyzed information.

FastAPI is the expected backend framework.

### Responsibilities

The API may serve:

* Current Assessment
* Historical Assessments
* Component scores
* Indicators
* Observations
* Metrics
* Signals
* Events
* Commentary
* Concepts
* Diagnostics
* Data-freshness status

### API Principles

* Business logic should live outside route handlers.
* API responses should use explicit schemas.
* Dates, units, and freshness information should be included.
* Errors should be clear and structured.
* Public and administrative endpoints should be separated.
* API behavior should be testable independently from the frontend.

### Initial Endpoints

Possible Version 1 endpoints include:

```text
GET /health
GET /api/v1/assessment/latest
GET /api/v1/indicators
GET /api/v1/indicators/{indicator_id}
GET /api/v1/indicators/{indicator_id}/observations
GET /api/v1/signals/active
GET /api/v1/commentary/morning-brief/latest
```

The exact API design will be documented separately.

---

## 4.11 Frontend

### Purpose

The frontend presents the Morning Brief, Assessment, component detail, Indicators, charts, Signals, and Concepts.

### Responsibilities

The frontend may:

* Request data from the API
* Display scores and condition labels
* Render charts
* Show data dates and freshness
* Provide drill-down navigation
* Display source and methodology information
* Present nuance and conflicting evidence
* Present educational Concept content

### Frontend Must Not

The frontend must not:

* Calculate official Metrics
* Trigger Signals
* Assign Assessment scores
* Generate market interpretations
* Replace missing data
* Embed hidden methodology

### Initial Frontend Approach

The current FastAPI-rendered HTML page may remain during early development.

A separate React or Next.js frontend should be introduced only when the added complexity is justified by:

* Rich interactive charts
* Reusable page components
* More extensive navigation
* Independent frontend deployment
* Public product design requirements

The architecture should allow this transition without rewriting the analytical backend.

---

# 5. Operational Workflow

## 5.1 Normal Daily Processing

A typical daily sequence is:

```text
1. Scheduled job begins.
2. Collectors retrieve newly available data.
3. Validation checks run.
4. Valid Observations are stored.
5. Affected Metrics are recalculated.
6. Relevant Events are loaded or updated.
7. Signal rules are evaluated.
8. Component Assessments are calculated.
9. Overall Assessment is calculated.
10. Confidence and data freshness are evaluated.
11. Commentary is generated.
12. Publication checks run.
13. The Assessment and Morning Brief are published.
14. Operational logs and diagnostics are recorded.
```

Not every Indicator updates daily. The pipeline must support mixed publication frequencies.

---

## 5.2 New York Fed Daily Rate Example

For SOFR:

```text
New York Fed publishes SOFR
        ↓
New York Fed Collector retrieves the record
        ↓
Validator checks required fields, date, rate and volume
        ↓
Observation is stored
        ↓
SOFR-related Metrics recalculate
        ↓
SOFR-related Signals reevaluate
        ↓
Funding Assessment recalculates
        ↓
Overall Assessment updates if required
        ↓
Morning Brief regenerates
        ↓
Website reflects the new publication
```

---

## 5.3 Weekly Federal Reserve Data Example

For reserve balances:

```text
Federal Reserve publishes H.4.1
        ↓
Federal Reserve Collector retrieves new data
        ↓
Validation confirms reporting period and units
        ↓
Observation is stored
        ↓
Weekly reserve-change Metrics recalculate
        ↓
Reserve Signals reevaluate
        ↓
Reserve Assessment updates
        ↓
Overall Assessment and Commentary update
```

The site must clearly disclose that reserve data are weekly and may lag daily market rates.

---

## 5.4 Historical Backfill

Historical data loading should use the same validation and storage rules as daily collection.

Backfill processing should:

* Run in manageable date ranges
* Record the source and retrieval date
* Avoid duplicate records
* Preserve revisions where available
* Recalculate dependent Metrics only after validated storage
* Produce an auditable completion report

---

## 5.5 Revised Data

When a source revises an Observation:

```text
Revised source record detected
        ↓
Revision stored without destroying prior provenance
        ↓
Affected Metrics recalculated
        ↓
Affected Signals reevaluated
        ↓
Affected Assessments optionally recomputed
        ↓
Revision impact recorded
```

The system should distinguish between:

* Correcting current operational outputs
* Preserving historically published Assessments
* Producing revised historical analysis

---

# 6. Failure Handling

## 6.1 Source Unavailable

Example: the New York Fed endpoint is temporarily unavailable.

Required behavior:

* Record the failed collection run.
* Retry according to policy.
* Preserve the latest valid Observation.
* Mark the Indicator as stale if the expected publication window passes.
* Reduce Assessment confidence if material.
* Display a data-freshness notice.
* Do not fabricate the missing value.

---

## 6.2 Source Publishes Late

Required behavior:

* Do not treat a late publication as a zero or unchanged value.
* Continue using the latest valid Observation.
* Mark the expected update as pending or stale.
* Determine whether the Assessment can still be published.
* Mention the delay when material.

---

## 6.3 Invalid Data

Examples:

* Missing required fields
* Non-numeric value
* Impossible date
* Rate outside a broad validation range
* Unexpected unit change

Required behavior:

* Reject or quarantine the affected Observation.
* Record the validation failure.
* Preserve the prior valid Observation.
* Prevent downstream calculations from using invalid data.
* Surface the issue in diagnostics.

---

## 6.4 Partial Data Availability

Example: SOFR and EFFR update, but Treasury data do not.

Required behavior:

* Recalculate unaffected Metrics and Signals.
* Mark affected component inputs stale or unavailable.
* Reduce confidence where appropriate.
* Preserve nuance about incomplete information.
* Avoid implying that all components reflect equally current data.

---

## 6.5 Database Unavailable

Required behavior:

* Do not publish a new Assessment.
* Preserve the last successfully published Assessment.
* Record and alert on the operational failure.
* Retry safely without creating duplicates.
* Avoid partially committed analytical results.

---

## 6.6 Metric or Signal Failure

Required behavior:

* Isolate the failed calculation.
* Record the methodology and input set involved.
* Prevent invalid outputs from entering the Assessment.
* Recalculate unaffected Metrics or Signals.
* Reduce confidence or withhold publication if the failed item is material.

---

## 6.7 Assessment Failure

Required behavior:

* Preserve the prior published Assessment.
* Do not publish a partial overall score as complete.
* Surface component-level results only if clearly labeled.
* Record the reason for failure.
* Allow deterministic reruns after correction.

---

## 6.8 Commentary Failure

Required behavior:

* Publish the validated Assessment without AI commentary.
* Use a deterministic fallback summary when possible.
* State that extended commentary is unavailable.
* Do not delay core data publication solely because AI failed.

---

# 7. Observability and Diagnostics

## 7.1 Purpose

The platform must make its operational state visible.

Operational problems should be diagnosable without manually inspecting many unrelated logs.

### Required Operational Information

For each Collector:

* Last attempted run
* Last successful run
* Source queried
* Duration
* Record count
* Success or failure
* Error message
* Retry count
* Latest available Observation date

For validation:

* Records validated
* Records accepted
* Records rejected
* Warnings
* Stale-data status

For analytics:

* Last Metric run
* Metrics calculated
* Failed Metrics
* Last Signal run
* Active Signals
* Resolved Signals
* Last Assessment run
* Methodology version
* Assessment publication status

For commentary:

* Last generation time
* Generation method
* Model or template version
* Evidence count
* Success or failure
* Review status

---

## 7.2 Diagnostics Endpoint

The application should eventually provide a restricted diagnostics endpoint or page.

Example:

```text
/admin/diagnostics
```

It may display:

```text
SOFR Collector                 Healthy
EFFR Collector                 Healthy
Reserve Balance Collector      Stale
Metric Engine                  Healthy
Signal Engine                  Healthy
Assessment Engine              Healthy
Commentary Engine              Degraded
Database                       Healthy
Last Published Assessment      2026-08-05 08:17 ET
```

Administrative access controls will be required before exposing detailed diagnostics publicly.

---

## 7.3 Logging

Google Cloud Logging is expected to be the production logging destination.

Logs should be structured where practical and include:

* Component
* Run identifier
* Indicator
* Effective date
* Methodology version
* Status
* Duration
* Error type
* Human-readable message

Sensitive credentials and secret values must never be logged.

---

## 7.4 Monitoring and Alerts

Later production monitoring should alert on:

* Repeated Collector failures
* Missed expected publications
* Database failures
* Assessment failures
* Stale critical Indicators
* Commentary failures
* Unexpectedly large data revisions
* Unusually long processing times

---

# 8. Scheduling and Orchestration

## 8.1 Initial Approach

Google Cloud Scheduler may trigger:

* Cloud Run jobs
* Secured FastAPI administrative endpoints
* Dedicated ingestion services

The precise production orchestration approach will be selected after the local data pipeline is working.

### Scheduling Principles

* Schedules should reflect actual publication timing.
* Daily and weekly Indicators should not be treated identically.
* Jobs should be safe to rerun.
* A failed run should not corrupt prior results.
* Each run should have a unique identifier.
* Downstream stages should only begin after required upstream stages succeed or are explicitly waived.

---

## 8.2 Possible Initial Schedule

Examples:

* New York Fed rates: weekday mornings after expected publication
* Treasury data: according to source publication schedule
* H.4.1 reserve data: weekly after release
* Event calendar: daily
* Assessment refresh: after material source updates
* Commentary generation: after successful Assessment publication

The final schedule will be documented in `data-sources.md`.

---

# 9. Deployment Architecture

## 9.1 Initial Development

Current local setup:

```text
VS Code
    ↓
Python virtual environment
    ↓
FastAPI application
    ↓
Local browser
```

The initial Cloud Run deployment provides a publicly accessible test URL.

---

## 9.2 Early Production Structure

A practical early architecture is:

```text
Cloud Scheduler
        ↓
Cloud Run Application or Cloud Run Job
        ↓
Cloud SQL PostgreSQL
        ↓
FastAPI API
        ↓
Web Frontend
```

Supporting services:

* Artifact Registry
* Cloud Build
* Secret Manager
* Cloud Logging
* Cloud Monitoring
* Cloud Storage, if required

---

## 9.3 Application Separation

Version 1 may operate as one deployable FastAPI service containing:

* API
* Basic frontend
* Collectors
* Analytical engines
* Administrative commands

As scale and complexity increase, the system may separate into:

```text
Web/API Service
Ingestion Job
Analytics Job
Commentary Job
Frontend Service
```

This separation should occur only when operational or scaling requirements justify it.

Prematurely creating many services would add unnecessary complexity.

---

## 9.4 Secrets

Secrets such as API keys must be stored in:

* Local `.env` files excluded from Git during development
* Google Secret Manager in production

Secrets must not appear in:

* Source code
* Git commits
* Logs
* Public frontend code
* Error responses

---

# 10. Proposed Codebase Structure

An initial scalable structure is:

```text
liquidity-monitor/
├── backend/
│   ├── __init__.py
│   ├── api/
│   ├── assessments/
│   ├── collectors/
│   ├── commentary/
│   ├── concepts/
│   ├── database/
│   ├── events/
│   ├── metrics/
│   ├── models/
│   ├── services/
│   ├── signals/
│   ├── validation/
│   └── main.py
│
├── frontend/
│   ├── components/
│   ├── pages/
│   ├── charts/
│   └── services/
│
├── docs/
│   ├── architecture.md
│   ├── domain-model.md
│   ├── home-page-spec.md
│   ├── mission.md
│   ├── philosophy.md
│   ├── data-sources.md
│   └── coding-standards.md
│
├── scripts/
├── tests/
├── main.py
├── requirements.txt
├── Procfile
└── README.md
```

The folder structure may evolve gradually. Empty folders should not be created merely to make the repository appear complete.

---

# 11. Testing Strategy

## 11.1 Collector Tests

Collectors should be tested using saved response fixtures and mocked HTTP requests.

Tests should cover:

* Valid responses
* Missing fields
* Invalid JSON
* Network failures
* Timeouts
* Empty responses
* Unexpected units
* Revised records

---

## 11.2 Validation Tests

Validation tests should cover:

* Accepted observations
* Duplicate observations
* Range failures
* Invalid dates
* Missing values
* Stale values
* Revision handling

---

## 11.3 Metric Tests

Metric tests should use small, known datasets with manually verified outputs.

Calculations involving:

* Basis points
* Rolling windows
* Percentiles
* Z-scores
* Missing observations

must receive particular attention.

---

## 11.4 Signal Tests

Each Signal rule should have tests for:

* No trigger
* Initial trigger
* Persistent trigger
* Severity change
* Resolution
* Missing inputs
* Event-adjusted interpretation

---

## 11.5 Assessment Tests

Assessment tests should verify:

* Component contributions
* Overall score calculation
* Condition label mapping
* Confidence adjustments
* Missing component behavior
* Conflicting Signal handling
* Methodology versioning

---

## 11.6 Commentary Tests

Commentary tests should verify:

* Evidence is included
* Unsupported claims are absent
* Missing data are disclosed
* Conflicting evidence is retained
* Fallback commentary works without AI

Exact wording should not be overtested when generative AI is used. Structural and factual requirements are more important.

---

## 11.7 API Tests

API tests should verify:

* Response schemas
* Status codes
* Missing resources
* Date filtering
* Data-freshness fields
* Administrative access controls
* Health and diagnostics behavior

---

# 12. Security and Access

## 12.1 Public Access

Public Version 1 may expose:

* Current Assessment
* Morning Brief
* Public Indicators
* Charts
* Concepts
* Methodology
* Source information

---

## 12.2 Restricted Access

Restricted administrative functions may include:

* Manual data reruns
* Backfills
* Diagnostics
* Methodology changes
* Commentary review
* Publication control
* Data correction workflows

These functions must not be publicly accessible without authentication.

---

## 12.3 Data Licensing

Before proprietary or subscription data are added, the platform must verify:

* Display rights
* Storage rights
* Redistribution restrictions
* User access restrictions
* Attribution requirements

Official public data do not eliminate the need to review source terms.

---

# 13. Performance and Scalability

Version 1 does not require complex distributed architecture.

Expected early scale:

* Dozens of Indicators
* Daily or weekly updates
* Moderate historical datasets
* Limited public traffic
* Small numbers of analytical jobs

PostgreSQL and Cloud Run should comfortably support this scale.

Optimization should focus first on:

* Correctness
* Maintainability
* Rerunnability
* Observability
* Clear caching behavior

More advanced infrastructure should be introduced only in response to demonstrated need.

---

# 14. Architecture Decisions

The following decisions are established for Version 1:

1. FastAPI will remain the backend framework.
2. Google Cloud Run will host the initial application.
3. Official primary data sources will be preferred.
4. Collectors will remain separate from analytical calculations.
5. Raw observations will remain separate from Metrics.
6. Signals will be deterministic and rule-based.
7. Scores will be assigned by the Assessment Engine, not AI.
8. AI will explain structured outputs but will not create them.
9. The frontend will not contain hidden business logic.
10. The system will preserve the last valid published Assessment during operational failures.
11. Data dates and freshness will be visible to users.
12. The system will begin as a simple application and separate into additional services only when justified.

---

# 15. Open Architecture Questions

The following matters remain open:

1. When PostgreSQL should replace local or temporary storage
2. Whether ingestion should run through Cloud Run Jobs or secured API endpoints
3. Whether the frontend remains FastAPI-rendered or moves to Next.js
4. Exact authentication approach for administrative tools
5. Historical vintage and revision-retention policy
6. Exact methodology-version storage design
7. Public API access and rate limits
8. Caching strategy
9. Commentary review and approval workflow
10. Alert-delivery architecture
11. Backup and disaster-recovery requirements
12. Whether the Assessment runs after every source update or on fixed publication windows

These decisions should be made when the related implementation work begins.

---

# 16. Definition of Architectural Success

The architecture succeeds when:

* A new Data Source can be added without changing unrelated analytical layers.
* A new Indicator can be collected and stored using established interfaces.
* A new Metric can be introduced without modifying the frontend.
* A new Signal can be added through documented rules.
* Assessment methodology can evolve through versioning.
* AI can fail without invalidating the underlying analysis.
* Every published conclusion can be traced to evidence.
* A failed component can be diagnosed and rerun independently.
* The platform can grow from a small prototype into an institutional product without requiring a complete redesign.
