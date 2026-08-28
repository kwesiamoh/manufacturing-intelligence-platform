# Stage 12C.2 — Causal Adaptive Alerting

## Why Stage 12C needed one revision

The initial Isolation Forest detected all four known failure events, but the
fixed February calibration threshold generated:

- 4.42 false alert episodes/day;
- 12.48% of holdout time in alert.

Monthly diagnostics showed clear temporal score drift. The median Isolation
Forest score moved from approximately -0.081 in February to positive values in
later months, and the upper score tail shifted materially as well.

Therefore the model itself is retained, but the fixed decision threshold is
replaced.

## Adaptive decision rule

For each current five-minute window:

1. take Isolation Forest anomaly scores from the preceding seven days;
2. exclude the most recent 24 hours from that history;
3. require at least three days of historical scores;
4. set the current threshold to the historical 99.5th percentile;
5. mark a raw anomaly when the current score exceeds that threshold;
6. issue an alert only when at least 3 of the trailing 4 windows are anomalous.

This is causal. Future scores are never used.

## Why the 24-hour exclusion lag matters

If a developing fault produces elevated scores for several hours, allowing those
scores immediately into the adaptive reference distribution would raise the
threshold during the same event.

The 24-hour lag makes the threshold adaptive to slower operating-regime drift
while reducing self-adaptation to the current developing incident.

## No failure-label threshold tuning

The known MetroPT failure events are used only after the adaptive rule has been
defined, to evaluate:

- event detection;
- >=2-hour early warning;
- lead time;
- false alert episodes/day;
- time spent in alert.

The threshold is not moved up or down to force all four events to be detected.

## Acceptance guidance

Preferred portfolio result:

- failure-event recall as high as possible without label tuning;
- false alert episodes/day below 0.5;
- time in alert below roughly 3%;
- useful multi-hour warning retained.

With only four independent failure incidents, event counts should be reported as
fractions such as `3/4` or `4/4`, not treated as a statistically precise
population percentage.
