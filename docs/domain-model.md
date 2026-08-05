# Liquidity Monitor Domain Model

## 1. Purpose

This document defines the core business objects used by Liquidity Monitor and the relationships among them.

The domain model separates:

1. Externally published data
2. Internally calculated metrics
3. Rule-based signals
4. Liquidity assessments
5. Data-grounded narrative commentary

This separation is essential to the transparency, reliability, and maintainability of the platform.

The domain model describes business concepts rather than database tables, APIs, or programming-language classes. Technical implementation will follow from this model.

---

## 2. Analytical Flow

Liquidity Monitor follows this analytical pipeline:

```text
Data Source
    ↓
Indicator
    ↓
Observation
    ↓
Metric
    ↓
Signal
    ↓
Liquidity Assessment
    ↓
Commentary and Morning Brief
```

Events and Concepts provide context throughout the process.

```text
Events ──────────────┐
                    ├──→ Signals and Assessments
Concepts ────────────┘
```

Raw data, calculations, interpretations, and narrative must remain distinguishable at every stage.

---

# 3. Core Objects

## 3.1 Data Source

### Definition

A Data Source represents an organization, publication, system, or endpoint from which Liquidity Monitor obtains information.

Examples include:

* Federal Reserve Bank of New York
* Board of Governors of the Federal Reserve System
* U.S. Department of the Treasury
* Federal Reserve Economic Data
* Depository Trust & Clearing Corporation

### Why It Exists

A Data Source establishes the origin and authority of each observation.

It allows the platform to disclose:

* Who published the data
* Where the data were retrieved
* How frequently the data are released
* Whether the source is primary or secondary
* Whether an alternative source is available

### Owns

A Data Source owns its identifying and retrieval metadata, including:

* Name
* Short name
* Description
* Source type
* Publisher
* Website or API location
* Expected publication schedule
* Time zone
* Primary or secondary source designation
* Active or inactive status

### References

A Data Source may publish many Indicators.

An Indicator may have:

* One primary Data Source
* One or more secondary or backup Data Sources

### Rules

* Primary official publishers should be preferred whenever practical.
* A source change must not silently alter the meaning of an Indicator.
* Source failures and stale data must be disclosed.
* Retrieval time and publication time must remain distinguishable.

---

## 3.2 Category

### Definition

A Category represents a major functional area of liquidity analysis.

Initial Categories are:

* Funding
* Reserves
* Treasury
* Collateral
* Credit
* Macro Liquidity

### Why It Exists

Categories organize Indicators, Metrics, Signals, and component Assessments according to how market participants think about liquidity.

The site should not be organized primarily around government agencies or data vendors. Users think in terms of funding, reserves, collateral, and Treasury conditions—not individual statistical releases.

### Owns

A Category owns:

* Name
* Description
* Display order
* Analytical purpose
* Active or inactive status

### References

A Category may contain many:

* Indicators
* Metrics
* Signals
* Concepts

Each component Liquidity Assessment is associated with one Category.

### Rules

* Categories should remain broad and stable.
* New Categories should only be created when an existing Category cannot reasonably contain the subject.
* Categories are analytical groupings, not data sources.

---

## 3.3 Indicator

### Definition

An Indicator represents an externally published measurement that provides information about U.S. cash-market liquidity.

Examples include:

* SOFR
* EFFR
* IORB
* Reserve balances
* ON RRP usage
* Treasury General Account
* Standing Repo Facility usage

An Indicator has a stable identity. Its values change through Observations.

### Why It Exists

The Indicator is the central representation of an externally produced data series.

It allows the platform to treat different market series consistently while preserving their individual meaning, frequency, units, and publication conventions.

### Owns

An Indicator owns its descriptive metadata, including:

* Stable identifier
* Display name
* Full name
* Description
* Category
* Primary Data Source
* Publication frequency
* Units
* Decimal precision
* Expected update schedule
* First available observation date
* Interpretation guidance
* Whether higher values generally indicate easier, tighter, or context-dependent liquidity
* Active or inactive status

### References

An Indicator:

* Belongs to one primary Category
* Has one primary Data Source
* May have secondary Data Sources
* Has many Observations
* May be used by many Metrics
* May contribute to many Signals
* May support many Assessments
* May be associated with one or more Concepts

### Rules

* Indicators represent externally published data, not internally calculated values.
* Indicator identity must remain separate from its observations.
* Missing data must not be silently estimated.
* Revisions must not overwrite historical provenance.
* The meaning and units of an Indicator must be explicit.

---

## 3.4 Observation

### Definition

An Observation is a published value for an Indicator for a specific observation period or date.

Example:

```text
Indicator: SOFR
Observation date: August 4, 2026
Value: 4.31%
Publisher: Federal Reserve Bank of New York
Release time: August 5, 2026 at 8:00 AM ET
```

### Why It Exists

Observations preserve the factual data used by the platform.

They form the historical record from which Metrics, Signals, charts, and Assessments are produced.

### Owns

An Observation owns:

* Indicator reference
* Observation date or period
* Value
* Units as published
* Publication timestamp, when available
* Retrieval timestamp
* Source reference
* Source-series identifier
* Revision or vintage information
* Data-quality status
* Validation status

### References

An Observation belongs to:

* One Indicator
* One Data Source publication record

An Observation may be used in:

* Metrics
* Signals
* Assessments
* Commentary evidence

### Rules

* Observation date and publication date must remain separate.
* Raw values should be preserved as received.
* Adjusted or transformed values belong in Metrics.
* Revised values must retain an auditable history where practical.
* Invalid, missing, or stale observations must be flagged rather than concealed.
* The platform must be able to determine what information was available at a particular point in time.

---

## 3.5 Metric

### Definition

A Metric is an internally calculated value derived from one or more Indicators, Observations, Metrics, or Events.

Examples include:

* SOFR minus EFFR
* SOFR minus IORB
* Weekly change in reserve balances
* 52-week percentile
* Rolling z-score
* Composite system-liquidity measure
* Persistence of a spread over several observations

### Why It Exists

Metrics transform raw observations into analytically useful comparisons and measures.

They help answer questions such as:

* Is the latest value unusual?
* How quickly is it changing?
* Is one market rate diverging from another?
* Is a movement persistent?
* How does the current environment compare with history?

### Owns

A Metric owns:

* Stable identifier
* Name
* Description
* Category
* Calculation methodology
* Input requirements
* Units
* Frequency
* Lookback period, when applicable
* Version
* Effective date
* Expected interpretation
* Validation rules

### References

A Metric may use:

* One or more Indicators
* One or more other Metrics
* A historical set of Observations
* Relevant Events

A Metric may contribute to:

* Signals
* Component Assessments
* Overall Liquidity Assessments
* Charts
* Commentary

### Rules

* Every Metric must have a documented and reproducible calculation.
* Methodology changes require a new version or effective date.
* Metrics must not be presented as externally published facts.
* Missing required inputs must produce an unavailable result rather than an invented value.
* Calculations must use data available as of the stated assessment time.
* Metrics should remain deterministic unless explicitly designated otherwise.

---

## 3.6 Event

### Definition

An Event represents a scheduled or observed occurrence that may affect liquidity conditions or the interpretation of market data.

Examples include:

* Month-end
* Quarter-end
* Corporate tax dates
* Treasury auction settlements
* Large Treasury maturities
* FOMC meetings
* Treasury Quarterly Refunding announcements
* Debt-limit episodes
* Unexpected market disruptions

### Why It Exists

Events provide context.

A change in SOFR may have a different interpretation at quarter-end than on an ordinary trading day. An increase in the Treasury General Account may be more meaningful when associated with tax receipts or large debt settlements.

### Owns

An Event owns:

* Name
* Event type
* Description
* Start date and time
* End date and time, when applicable
* Expected or observed designation
* Expected liquidity effect
* Actual liquidity effect, when known
* Importance level
* Source
* Status

### References

An Event may relate to many:

* Indicators
* Metrics
* Signals
* Assessments
* Commentary items

### Rules

* Scheduled and observed Events must be distinguishable.
* Expected effects must not be presented as confirmed outcomes.
* Events should provide context, not automatically determine conclusions.
* Event significance may differ across Categories.
* Historical events should remain available for comparison.

---

## 3.7 Signal

### Definition

A Signal is a rule-based finding that identifies a noteworthy condition, change, divergence, threshold crossing, or pattern in the data.

Examples include:

* SOFR has traded above EFFR for five consecutive sessions.
* Reserve balances reached a two-year low.
* SOFR volume moved into the top historical decile.
* The TGA increased by more than $75 billion in one week.
* SRF usage became positive.
* Funding and reserve indicators are moving in conflicting directions.

### Why It Exists

Not every Observation or Metric deserves attention.

Signals identify the developments most likely to matter for the Liquidity Assessment and Morning Brief.

They provide a structured bridge between calculations and interpretation.

### Owns

A Signal owns:

* Stable signal definition
* Name
* Description
* Category
* Detection rule
* Severity
* Direction
* Start time
* End time, when resolved
* Persistence
* Supporting evidence
* Status
* Rule version

### References

A Signal may be based on:

* Indicators
* Observations
* Metrics
* Events
* Other Signals

A Signal may contribute to:

* Component Assessments
* Overall Liquidity Assessments
* Nuance highlights
* Commentary
* Future alerts

### Rules

* Signals are generated by documented rules, not generative AI.
* A Signal must cite the evidence that triggered it.
* Signal severity must be distinct from certainty.
* Temporary calendar effects should be identified where possible.
* Conflicting Signals must be retained and disclosed.
* A Signal may affect the narrative without materially changing the overall score.

---

## 3.8 Liquidity Assessment

### Definition

A Liquidity Assessment is a time-specific evaluation of liquidity conditions based on validated Indicators, Metrics, Signals, and relevant Events.

The Assessment is the principal analytical output of Liquidity Monitor.

It includes:

* An overall score
* An overall condition
* Component scores
* Key positive and negative contributors
* Nuances and conflicting evidence
* Confidence
* Items to monitor next

### Why It Exists

The Liquidity Assessment converts a large collection of data into a concise, explainable view of current conditions.

It answers:

1. What is the current state of liquidity?
2. What changed?
3. Why did it change?
4. How unusual is it?
5. What should the user watch next?

### Owns

A Liquidity Assessment owns:

* Assessment date and time
* Data cutoff time
* Overall score
* Overall condition
* Change from the previous Assessment
* Component scores
* Component conditions
* Confidence level
* Summary rationale
* Positive contributors
* Negative contributors
* Nuances
* Conflicting evidence
* Data-freshness status
* Methodology version
* Publication status

### Component Assessments

Initial components are:

* Funding
* Reserves
* Treasury
* Collateral
* Credit

Macro Liquidity may provide context without initially receiving an independent component score.

### Overall Score

The overall score is intended to provide rapid orientation.

An example presentation is:

```text
78 / 100 — Normal
```

The score must not conceal important disagreement among components.

For example:

```text
Overall:     78 — Normal
Funding:     91 — Healthy
Reserves:    54 — Tightening
Treasury:    77 — Normal
Collateral:  86 — Healthy
Credit:      82 — Healthy
```

The accompanying assessment should highlight that reserve conditions are materially weaker than the other components.

### Condition Labels

Initial condition labels are:

* Abundant
* Normal
* Tightening
* Stressed
* Severe Stress

Exact score ranges will be defined in the scoring methodology rather than in this domain model.

### Confidence

Confidence describes confidence in the interpretation, not confidence in the official source data.

Initial confidence labels are:

* High
* Moderate
* Low

Confidence may be reduced by:

* Stale data
* Missing inputs
* Conflicting Signals
* Short history
* Unusual structural changes
* Heavy reliance on lagged indicators

### References

A Liquidity Assessment uses:

* Indicators
* Metrics
* Signals
* Events
* Prior Assessments
* Methodology versions

It supports:

* Morning Briefs
* Home-page summaries
* Historical comparisons
* Commentary
* Future notifications

### Rules

* The Assessment must be reproducible from its inputs and methodology version.
* The score must be explainable through component contributions.
* Nuance must not be suppressed merely because the headline score is stable.
* Conflicting evidence must be disclosed.
* Missing or stale data must reduce confidence where appropriate.
* AI may explain an Assessment but may not independently assign its score.
* Historical comparisons must avoid implying forecasts unless explicitly supported.
* The Assessment must distinguish current conditions from expected future risks.

---

## 3.9 Commentary

### Definition

Commentary is a written explanation of validated data, Metrics, Signals, Events, and Assessments.

Commentary may be generated through deterministic templates, generative AI, human review, or a combination of these methods.

### Why It Exists

Commentary explains:

* What changed
* Why it may have changed
* Whether it matters
* How the evidence fits together
* What remains uncertain
* What should be monitored next

### Owns

Commentary owns:

* Commentary type
* Publication date and time
* Assessment reference
* Text
* Supporting evidence references
* Generation method
* Model or template version
* Review status
* Confidence statement
* Publication status

### Commentary Types

Initial types include:

* Morning Brief
* Category Summary
* Indicator Commentary
* Signal Explanation
* Historical Comparison
* Data-quality notice

### References

Commentary may reference:

* Assessments
* Indicators
* Observations
* Metrics
* Signals
* Events
* Concepts

### Rules

* Commentary must be grounded in available validated evidence.
* It must distinguish fact from interpretation.
* It must not invent market sentiment or causal explanations.
* It must acknowledge conflicting or inconclusive evidence.
* It must disclose stale or incomplete data when material.
* It must avoid investment recommendations.
* AI-generated text must not modify raw data, Metrics, Signals, or scores.
* Supporting evidence should be available to the user.

---

## 3.10 Concept

### Definition

A Concept represents the meaning, mechanics, and educational context of a liquidity-related subject.

Examples include:

* Secured overnight funding
* Reserve balances
* Treasury General Account
* Quantitative tightening
* Repo market
* Standing Repo Facility
* Collateral scarcity

An Indicator has values. A Concept has meaning.

### Why It Exists

Concepts allow Liquidity Monitor to function as both an analytical platform and a knowledge base.

They help users understand:

* What something is
* Why it exists
* How it affects liquidity
* How it relates to other subjects
* Which historical episodes illustrate its importance

### Owns

A Concept owns:

* Name
* Definition
* Explanation
* Why it matters
* Related Concepts
* Related Indicators
* Historical examples
* Frequently asked questions
* Methodology references
* Educational content
* Review status

### References

A Concept may relate to:

* Indicators
* Metrics
* Events
* Signals
* Commentary
* Other Concepts

### Rules

* Concepts should remain useful across market cycles.
* Educational content must distinguish general mechanics from current conditions.
* Related Concepts should form a navigable knowledge graph.
* Concept content should be reviewed separately from daily market Commentary.

---

# 4. Object Relationships

## Data Source and Indicator

* A Data Source publishes many Indicators.
* An Indicator has one primary Data Source.
* An Indicator may have multiple backup or secondary Data Sources.

## Indicator and Observation

* An Indicator has many Observations.
* An Observation belongs to one Indicator.
* The Indicator defines meaning; the Observation provides the dated value.

## Indicator and Metric

* A Metric may use one or more Indicators.
* An Indicator may be used by many Metrics.

## Metric and Signal

* A Signal may depend on one or more Metrics.
* A Metric may contribute to many Signals.

## Event and Signal

* An Event may provide context for a Signal.
* A Signal may identify that a movement is consistent with or unusual for an Event.

## Signal and Liquidity Assessment

* A Liquidity Assessment may use many Signals.
* A Signal may affect one or more component Assessments.
* A Signal may be highlighted as a nuance without materially changing the score.

## Assessment and Commentary

* A Liquidity Assessment may have multiple Commentary outputs.
* Commentary explains the Assessment but does not determine its score.

## Concept and Other Objects

* A Concept may explain Indicators, Metrics, Events, and Signals.
* Concepts connect analytical data with educational context.

---

# 5. Separation of Analytical Layers

The system must preserve the distinction among the following layers.

## Raw Fact

```text
SOFR = 4.31%
```

Represented by:

* Indicator
* Observation
* Data Source

## Calculation

```text
SOFR minus EFFR = 3 basis points
```

Represented by:

* Metric

## Noteworthy Finding

```text
SOFR has exceeded EFFR for five consecutive sessions.
```

Represented by:

* Signal

## Evaluation

```text
Funding conditions remain Normal.
```

Represented by:

* Liquidity Assessment

## Explanation

```text
The persistent positive spread warrants attention, although funding volumes and facility usage do not currently indicate broader stress.
```

Represented by:

* Commentary

These layers must never be silently merged.

---

# 6. Version 1 Scope

Version 1 will initially support the following objects:

* Data Source
* Category
* Indicator
* Observation
* Metric
* Event
* Signal
* Liquidity Assessment
* Commentary
* Concept

Initial Indicators will include:

* SOFR
* EFFR
* IORB
* SOFR transaction volume
* Reserve balances
* ON RRP usage
* Treasury General Account
* Standing Repo Facility usage

Initial Metrics will include:

* SOFR minus EFFR
* SOFR minus IORB
* EFFR minus IORB
* Daily and weekly changes
* Historical percentiles
* Rolling z-scores
* Basic persistence measures

Initial Categories will include:

* Funding
* Reserves
* Treasury
* Collateral
* Credit

Some Categories may initially have limited data and may not receive a score until sufficient Indicators and methodology are available.

---

# 7. Principles Governing the Domain Model

1. Raw data, calculations, Signals, Assessments, and Commentary remain distinct.
2. Official primary data sources are preferred whenever practical.
3. Every calculation must be documented and reproducible.
4. Every Signal must identify its supporting evidence.
5. Every Assessment must disclose its component contributions.
6. A headline score must not suppress material nuance.
7. Conflicting evidence must be retained and explained.
8. Missing or stale data must never be hidden.
9. AI may explain structured analysis but may not independently create facts, Metrics, Signals, or scores.
10. Historical context should inform interpretation without being presented as a forecast.
11. The model should accommodate new Indicators without requiring structural redesign.
12. The platform should clearly distinguish what is known, what is calculated, and what is interpreted.

---

# 8. Future Extensions

The domain model should later accommodate:

* Global liquidity regions
* Securities-lending data
* Dealer balance-sheet indicators
* Treasury market depth
* FICC clearing activity
* User-defined watchlists
* Alerts and notifications
* Research publications
* Scenario analysis
* Portfolio liquidity analytics
* Methodology approval workflows
* Human commentary review
* Paid or restricted datasets

These extensions should build upon the existing objects rather than replace them.

---

# 9. Open Design Questions

The following matters will be addressed in later documents:

1. Exact scoring ranges for condition labels
2. Component weights in the overall Liquidity Score
3. Rules for handling stale or missing data
4. Confidence-level calculation
5. Signal severity definitions
6. Assessment publication schedule
7. Historical comparison methodology
8. Data-vintage and revision policy
9. Human-review requirements for Commentary
10. Whether Macro Liquidity receives a formal component score
11. Database implementation
12. API structure
13. Frontend presentation

---

# 10. Definition of Success

The domain model succeeds if Liquidity Monitor can add a new liquidity series without redesigning the platform.

Adding a new Indicator should generally require:

1. Defining its metadata
2. Connecting its Data Source
3. Loading and validating its Observations
4. Defining relevant Metrics
5. Defining relevant Signals
6. Assigning it to a Category
7. Documenting its associated Concept
8. Determining whether it contributes to an Assessment

The platform should then already know how to store, retrieve, chart, explain, and incorporate the new information into its broader analytical framework.
