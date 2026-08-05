# Liquidity Monitor — Home Page Specification

## Purpose

The home page should allow a user to understand the condition of U.S. cash-market liquidity in approximately 30 seconds.

It should answer:

1. Are liquidity conditions normal, tightening, or stressed?
2. What changed most recently?
3. Where is pressure appearing?
4. What should the user monitor next?

---

## Page Sections

### 1. Header

Display:

- Liquidity Monitor
- U.S. Cash Market Conditions
- Last successful data update
- Data freshness status

Example:

> Updated August 5, 2026 at 8:15 AM ET

---

### 2. Current Liquidity Assessment

Display one overall condition:

- Abundant
- Normal
- Tightening
- Stressed
- Severe Stress

Version 1 will initially use a manually assigned status.

Later versions will calculate the status from underlying indicators.

Display:

- Overall condition
- Liquidity score
- Change from prior day
- Short explanation

Example:

> Normal — Funding markets remain orderly, although reserve balances declined during the latest reporting week.

---

### 3. Core Market Indicators

Display cards for:

- SOFR
- EFFR
- IORB
- SOFR minus EFFR
- SOFR minus IORB
- SOFR transaction volume

Each card should include:

- Latest value
- Change from prior observation
- Observation date
- Status indicator
- Small historical trend chart

---

### 4. System Liquidity Indicators

Display cards for:

- Reserve balances
- Treasury General Account
- ON RRP
- Standing Repo Facility usage

Each card should show:

- Latest value
- Weekly change
- Directional liquidity effect
- Observation date

Directional examples:

- Rising reserves: liquidity positive
- Rising TGA: liquidity negative
- Falling ON RRP: depends on destination of cash
- Rising SRF usage: possible funding pressure

---

### 5. What Changed

Display the three most important changes since the prior update.

Example:

1. SOFR increased 3 basis points.
2. The Treasury General Account rose by $48 billion.
3. Reserve balances declined by $35 billion.

Initially, this can be rule-based rather than AI-generated.

---

### 6. Market Commentary

Display a short paragraph summarizing current conditions.

The commentary should:

- Explain movements rather than merely repeat values
- Distinguish temporary calendar effects from persistent pressure
- Mention conflicting indicators
- Avoid making investment recommendations
- State when data are stale or incomplete

---

### 7. Recent Trends

Include historical charts for:

- SOFR, EFFR and IORB
- SOFR minus EFFR
- Reserve balances
- TGA and ON RRP
- Composite system liquidity

Default chart period:

- One year

Available periods later:

- One month
- Three months
- One year
- Five years
- Maximum history

---

### 8. Upcoming Liquidity Events

Display important scheduled events:

- Treasury settlements
- Treasury tax dates
- Month-end
- Quarter-end
- FOMC meetings
- Large Treasury maturities
- Quarterly Refunding announcements

This will be added after the initial data dashboard is working.

---

## Version 1 Data

The first functioning home page will use:

- SOFR
- EFFR
- IORB
- SOFR transaction volume
- Reserve balances
- ON RRP
- Treasury General Account
- Standing Repo Facility usage

---

## Version 1 Exclusions

The following will not be included initially:

- User accounts
- Paid subscriptions
- Securities-lending data
- Treasury market depth
- FICC clearing statistics
- Intraday market data
- Email alerts
- Proprietary datasets

---

## Design Principles

- Institutional rather than promotional
- Clear rather than visually crowded
- Data dates must always be visible
- Every metric must include a source
- Missing data must never be silently replaced
- AI commentary must be based only on available validated data