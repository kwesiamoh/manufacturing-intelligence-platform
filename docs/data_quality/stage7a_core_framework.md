# Stage 7A — Core data quality framework

## Purpose

Stage 7A creates a reusable rule/result structure instead of leaving quality checks scattered through individual validation scripts.

## Dimensions of data quality covered

- completeness
- uniqueness
- validity
- consistency
- referential integrity

## Initial domains

- production
- downtime
- quality
- maintenance
- energy
- external benchmark prices

## Scoring

Each rule records:
- rows evaluated
- rows failed
- failure rate
- PASS / FAIL

The domain and enterprise score is:

`1 - failed rows / evaluated rows`

This is a technical quality score for the checked records, not a claim that the entire source is objectively 100% high quality.

## Important limitation

Stage 7A focuses on structured enterprise facts and benchmark data.

Sensor-stream quality checks such as:
- timestamp gaps
- frozen signals
- sensor spikes
- missing telemetry windows

will be added in Stage 7B against the real telemetry datasets, because those checks need time-series-specific logic and should not be fabricated against shift-level transactional data.
