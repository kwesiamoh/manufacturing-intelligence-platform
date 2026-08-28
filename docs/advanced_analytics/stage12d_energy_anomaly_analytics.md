# Stage 12D — Contextual Energy Anomaly Analytics

This stage detects shifts whose line electricity use is unusual relative to
their operating context.

## Provenance
Source: `SYNTHETIC_ENTERPRISE`, a fictional enterprise integration layer.
Results demonstrate the workflow and are not measured plant evidence.

## Design
Target: `line_total_electricity_kwh` per shift.

Context variables include site, line, product, shift, production volume,
operating time, planned production time, nominal/actual rate, and air
temperature.

Time split:
- first 80% of 2024: model training
- final 20% of 2024: anomaly-threshold calibration
- 2025: untouched monitoring/holdout

The expected-energy model is a HistGradientBoosting regressor. For every shift:

`residual_kWh = actual_kWh - expected_kWh`

`residual_% = residual_kWh / expected_kWh`

Calibration residuals are evaluated separately by line. The 0.5th and 99.5th
percentiles define unusual low/high energy use. `HIGH_ENERGY` is the primary
energy-waste investigation signal.

Model quality is evaluated on 2025 with MAE, RMSE, R², and MAPE. Anomaly rates
and excess kWh are reported separately.

A high-energy anomaly is an investigation flag, not proof of equipment failure.

## Run
```powershell
python -m pip install -r .\scripts\requirements_stage12d.txt
python .\scripts\run_stage12d_energy_anomaly.py
```
