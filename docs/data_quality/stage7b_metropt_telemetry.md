# Stage 7B — MetroPT telemetry data quality

## Why Stage 7B may produce warnings

Real telemetry should not be forced to look perfect.

Stage 7B separates:
- structural DQ failures;
- time-series findings requiring investigation.

### FAIL

Used for:
- missing timestamps;
- duplicate timestamps.

### WARN

Used when observed for:
- cadence gaps;
- missing sensor values;
- frozen continuous signals;
- abrupt robust-statistical spikes.

Warnings do not automatically mean the source is wrong.

For example:
- a long constant pressure may be operationally valid;
- a large first difference may be a genuine machine-state transition;
- a sampling gap may reflect maintenance or source-system downtime.

These findings become investigation candidates.

## Cadence gaps

The normal interval is derived from the data median rather than hard-coded.

A gap is defined as:

`interval > 1.5 × median interval`

MetroPT is expected to be approximately 10-second data, so this will normally correspond to an interval above 15 seconds.

## Frozen signals

Only continuous numeric channels are checked.

Known discrete/status channels are excluded.

A frozen event is an unchanged continuous value lasting at least 10 minutes.

This threshold is operational screening, not proof of sensor failure.

## Spike detection

Spikes are screened from first differences using a robust Median Absolute Deviation rule:

`|delta - median(delta)| > 8 × MAD(delta)`

This is deliberately conservative.

The results should be treated as candidates for inspection, not automatically deleted or corrected.

## Outputs

Detailed findings are written under:

`data_quality/metropt/`

The PostgreSQL `dq_result` table stores aggregate rule results for reporting.

## Scope

Stage 7B begins with MetroPT-3 because it is the project's large real continuous telemetry source.

Other reference datasets can receive source-specific checks later only where those checks materially support the final analytics.
