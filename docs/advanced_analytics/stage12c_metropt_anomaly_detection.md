# Stage 12C — MetroPT-3 Telemetry Anomaly Detection

## Purpose

Stage 12C adds a real-data anomaly-detection workflow using MetroPT-3 telemetry.

This analysis is deliberately kept separate from the fictional six-site
enterprise integration layer. The PostgreSQL `fact_telemetry` table is empty,
so no claim is made that MetroPT telemetry originated from the fictional
beverage enterprise.

## Locked design

### Time resolution

Raw Silver observations are approximately 10 seconds apart.

They are aggregated into **causal 5-minute bins**. A valid bin must contain at
least 80% of the expected raw observations.

### Inputs

Continuous channels:

- TP2
- TP3
- H1
- DV pressure
- reservoirs
- oil temperature
- motor current

Discrete operating-state channels:

- COMP
- DV electric
- Towers
- MPG
- LPS
- Pressure switch
- Oil level
- Caudal impulses

Digital channels are used as operating-state context rather than treated as
continuous physical measurements.

### Features

Five-minute continuous-channel features include:

- mean
- standard deviation
- minimum
- maximum
- last value
- range
- mean absolute first difference
- within-bin change

Discrete-channel features include:

- active proportion
- transition count
- final state

A trailing **60-minute causal context** is then added. No future observation is
used to construct a feature for the current timestamp.

### Data splitting

The first calendar month is used for model development:

- first 70%: training
- final 30%: calibration

Known failure windows and a 24-hour buffer around them are excluded from
training/calibration.

All later months are strict holdout data.

### Model

Primary model: **Isolation Forest**

- 300 trees
- robust median/IQR scaling
- random state fixed at 42
- model fitted on training windows only

Threshold:

- 99.5th percentile of anomaly scores on the calibration period
- failure outcomes are not used to choose this threshold

A transparent robust-z detector is retained as a reference baseline.

### Alert persistence

A raw anomaly does not immediately become an operational alert.

An alert requires at least **3 anomalous five-minute bins out of the trailing 4**.

This reduces isolated noisy alerts while remaining causal.

## Evaluation

The primary evaluation unit is the **failure event**, not individual timestamps.

For each held-out failure, the pipeline reports:

1. whether an alert occurs in the 24 hours before the failure or during it;
2. whether the failure is detected at least 2 hours early;
3. first-alert lead time.

Operational burden is measured by:

- false alert episodes per day;
- percentage of holdout time spent in alert.

Window-level PR-AUC is reported only as a secondary metric.

Accuracy is intentionally not used as the primary metric because the timeline
is strongly imbalanced toward normal operation.

## Output

The pipeline writes:

```text
data/gold/advanced_analytics/metropt_anomaly/
    metropt_anomaly_windows.parquet
    metropt_alert_episodes.csv
    metropt_failure_event_evaluation.csv

reports/advanced_analytics/
    stage12c_telemetry_anomaly_metrics.json
    stage12c_feature_columns.txt

models/advanced_analytics/metropt/
    robust_scaler.joblib
    isolation_forest.joblib
```

## Run

Install requirements if needed:

```powershell
python -m pip install -r .\scripts\requirements_stage12c.txt
```

Then:

```powershell
python .\scripts\run_stage12c_metropt_anomaly.py
```

Review the printed holdout metrics before accepting the model.

## Interpretation rule

A high anomaly score means the multivariate telemetry state differs from the
normal training regime. It does not by itself prove a mechanical fault.

The known MetroPT failure windows are used to evaluate whether alerts are
operationally meaningful.

## Data-quality separation

Existing gap, frozen-signal, and spike diagnostics remain data-quality
diagnostics. They are not automatically re-labelled as equipment failures.
