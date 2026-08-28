# Stage 13E.2 — Hydraulic Condition Classification

## Purpose

Stage 13E.2 uses the real `HYDRAULIC_CM` source for cycle-level condition
classification.

The source remains completely separate from the synthetic beverage-enterprise
maintenance and downtime layer.

## Feature engineering

The normalized telemetry contains tens of millions of raw samples but only
2,205 independent cycles.

Each sensor trace is therefore reduced to six cycle-level statistics:

- mean
- standard deviation
- minimum
- maximum
- range
- RMS

With 17 sensors this yields 102 engineered features per cycle.

This avoids treating millions of within-cycle samples as millions of
independent training observations.

## Targets

Physical-condition models:

- cooler condition
- valve condition
- internal pump leakage
- hydraulic accumulator pressure

These are evaluated on cycles where `stable_flag = 1`, because the source
explicitly indicates that unstable cycles may not have reached static
conditions.

`stable_flag` is modeled separately on all cycles.

## Validation design

The final 20% of cycles are held out in cycle order.

This is intentionally stricter than a random split and reduces the chance that
adjacent, highly similar operating cycles are split across train and test.

## Model

Extra Trees classifier:

- nonlinear
- works well with mixed sensor-statistic features
- no aggressive scaling required
- supports class weighting
- provides feature importance

## Metrics

Primary:
- macro F1
- balanced accuracy

Secondary:
- ordinary accuracy

A majority-class baseline is reported for every target.

## Interpretation

This stage demonstrates **condition classification**.

It does not claim:
- failure forecasting
- remaining useful life
- beverage-plant predictive maintenance

## Run

```powershell
python -m pip install -r .\scripts\requirements_stage13e2.txt
python .\scripts\run_stage13e2_hydraulic_condition_classification.py
```

The first run creates the cycle-feature Parquet. Later runs reuse it.
