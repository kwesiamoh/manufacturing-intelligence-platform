# Stage 12E — Production and Energy Forecasting

## Purpose

Stage 12E adds a limited forecasting workflow for:

- daily production output;
- daily site electricity demand.

The goal is to demonstrate time-series validation rather than to build a large
forecasting platform.

## Provenance

The source is `SYNTHETIC_ENTERPRISE`, the fictional six-site integration layer.
Forecast accuracy is therefore portfolio-method evidence, not measured-plant
performance.

## Forecast grain

Site-day.

## Forecast horizon

One day ahead.

This means each prediction may use actual observations from prior days, but
never the current/future target value.

## Features

For each target:

- lags: 1, 7, 14, 28 days;
- trailing rolling mean: 7 and 28 days;
- trailing rolling standard deviation: 7 and 28 days;
- site;
- day of week;
- day of month;
- month;
- week of year;
- weekend flag.

Rolling statistics are shifted by one day before calculation, so they are
strictly causal.

## Holdout

The final 60 calendar days of 2025 are held out for evaluation.

## Models

Two forecasts are compared:

1. HistGradientBoostingRegressor
2. Seasonal naive: same site, seven days earlier

The model with lower holdout MAE is selected separately for production and
energy.

This baseline comparison is important: a machine-learning forecast is not
considered useful merely because it produces a low error. It should improve on
a simple seasonal reference.

## Metrics

- MAE
- RMSE
- R²
- MAPE

## Interpretation

This is an operational rolling one-day-ahead evaluation.

It is **not** a claim that the model can recursively forecast the next 60 days
from a single starting date with the same error.

## Run

```powershell
python -m pip install -r .\scripts\requirements_stage12e.txt
python .\scripts\run_stage12e_forecasting.py
```
