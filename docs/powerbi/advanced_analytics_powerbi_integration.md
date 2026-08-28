# Power BI Advanced-Analytics Integration

## Import these four views

From PostgreSQL `manufacturing_intelligence`:

- `gold_bi.vw_site_daily_forecast`
- `gold_bi.vw_shift_energy_anomaly`
- `gold_bi.vw_monthly_reliability_trend`
- `gold_bi.vw_monthly_equipment_type_reliability_trend`

## Relationships

Use single-direction, one-to-many dimension relationships.

### Forecast

- `dim_time[calendar_date]` 1 -> * `vw_site_daily_forecast[calendar_date]`
- `dim_site[site_id]` 1 -> * `vw_site_daily_forecast[site_id]`

### Energy anomaly

- `dim_time[calendar_date]` 1 -> * `vw_shift_energy_anomaly[calendar_date]`
- `dim_site[site_id]` 1 -> * `vw_shift_energy_anomaly[site_id]`
- `dim_line[line_id]` 1 -> * `vw_shift_energy_anomaly[line_id]`

### Reliability

- `dim_time[calendar_date]` 1 -> * `vw_monthly_reliability_trend[calendar_date]`
- `dim_site[site_id]` 1 -> * `vw_monthly_reliability_trend[site_id]`
- `dim_line[line_id]` 1 -> * `vw_monthly_reliability_trend[line_id]`

Equipment-type reliability:
- Date and Site relationships only.

Do not create fact-to-fact relationships.

## Forecast measures

```DAX
Production Forecast Actual =
CALCULATE(
    SUM(vw_site_daily_forecast[actual_value]),
    vw_site_daily_forecast[forecast_domain] = "PRODUCTION"
)

Production Forecast =
CALCULATE(
    SUM(vw_site_daily_forecast[selected_forecast_value]),
    vw_site_daily_forecast[forecast_domain] = "PRODUCTION"
)

Production Forecast Error =
[Production Forecast Actual] - [Production Forecast]

Production Forecast MAPE =
CALCULATE(
    AVERAGE(vw_site_daily_forecast[absolute_pct_error_pct]),
    vw_site_daily_forecast[forecast_domain] = "PRODUCTION"
)

Energy Forecast Actual =
CALCULATE(
    SUM(vw_site_daily_forecast[actual_value]),
    vw_site_daily_forecast[forecast_domain] = "ENERGY"
)

Energy Forecast =
CALCULATE(
    SUM(vw_site_daily_forecast[selected_forecast_value]),
    vw_site_daily_forecast[forecast_domain] = "ENERGY"
)

Energy Forecast Error =
[Energy Forecast Actual] - [Energy Forecast]

Energy Forecast MAPE =
CALCULATE(
    AVERAGE(vw_site_daily_forecast[absolute_pct_error_pct]),
    vw_site_daily_forecast[forecast_domain] = "ENERGY"
)
```

`absolute_pct_error_pct` retains its existing compatibility name, but its stored
value is a **fractional ratio**: for example, approximately `0.0072` represents
`0.72%`. This follows the Stage 12E calculation `absolute_error / actual_value`
and the accepted Parquet values. Do not divide it by 100 again.

Keep both MAPE measures numeric and format them as Percentage with two decimal
places in Power BI. The accepted snapshot displays approximately `0.72%` for
Production and `0.51%` for Energy. `FORMAT()` is unnecessary for the canonical
measure; it may be used only for a separate display-only text measure.

## Rerunnable PostgreSQL landing refresh

`scripts/load_powerbi_advanced_analytics.py` validates and hashes both accepted
Parquet inputs before connecting to PostgreSQL. Unknown forecast targets fail;
the only accepted mappings are:

- `daily_actual_quantity` -> `PRODUCTION`
- `daily_site_total_electricity_kwh` -> `ENERGY`

Landing tables have stable definitions. A refresh uses transactional `TRUNCATE`
and `COPY`, so dependent `gold_bi` views are never dropped. Constraints,
dimension-key checks, corrected-reliability checks, and post-load counts execute
before commit. Any failure rolls back the transaction and restores the prior
landing rows. Corrected reliability downtime is checked against `14,856.65`
hours with an explicit `+/- 0.01` hour tolerance to avoid exact binary
floating-point comparison.

Each successful load writes input paths, SHA-256 checksums, row counts, and the
acceptance summary to `analytics.bi_advanced_analytics_load_audit`. Input paths
may be overridden with `--forecast-path` and `--anomaly-path`. Use
`--validate-only` to validate and hash the Parquet files without contacting
PostgreSQL.

The energy-anomaly artifact physically contains one row per production shift,
uniquely identified by `production_id` and Date+Site+Line+Shift. Its Power BI
relationship dimensions remain Date, Site, and Line; no fact-to-fact
relationship is introduced. Forecast series remain Date+Site grain within each
forecast domain. Product and Shift are not forecast dimensions.

The equipment-type reliability view is physically one row per
Date+Site+EquipmentType; its Power BI relationship keys remain Date and Site
only, with equipment type used as an attribute/axis rather than a separate
relationship dimension.

## Energy anomaly measures

```DAX
Monitored Energy Shifts =
COUNTROWS(vw_shift_energy_anomaly)

High Energy Anomalies =
CALCULATE(
    COUNTROWS(vw_shift_energy_anomaly),
    vw_shift_energy_anomaly[is_high_energy_anomaly] = TRUE()
)

Low Energy Anomalies =
CALCULATE(
    COUNTROWS(vw_shift_energy_anomaly),
    vw_shift_energy_anomaly[is_low_energy_anomaly] = TRUE()
)

High Energy Anomaly Rate =
DIVIDE([High Energy Anomalies], [Monitored Energy Shifts])

High Energy Excess kWh =
CALCULATE(
    SUM(vw_shift_energy_anomaly[residual_kwh]),
    vw_shift_energy_anomaly[is_high_energy_anomaly] = TRUE()
)

Expected Line Energy kWh =
SUM(vw_shift_energy_anomaly[expected_kwh])

Actual Line Energy kWh =
SUM(vw_shift_energy_anomaly[line_total_electricity_kwh])
```

Format anomaly rate as Percentage.

## Reliability measures

```DAX
Corrective Failures =
SUM(vw_monthly_reliability_trend[corrective_failure_count])

Corrective Downtime h =
SUM(vw_monthly_reliability_trend[corrective_downtime_hours])

Reliability Operating Hours =
SUM(vw_monthly_reliability_trend[line_operating_hours])

Failures per 1000 Operating h =
DIVIDE(
    [Corrective Failures] * 1000,
    [Reliability Operating Hours]
)

Operating MTBF Proxy h =
DIVIDE(
    [Reliability Operating Hours],
    [Corrective Failures]
)

Weighted MTTR h =
DIVIDE(
    SUMX(
        vw_monthly_reliability_trend,
        vw_monthly_reliability_trend[mttr_hours]
            * vw_monthly_reliability_trend[corrective_failure_count]
    ),
    [Corrective Failures]
)

Corrective Downtime Ratio =
DIVIDE(
    [Corrective Downtime h],
    [Reliability Operating Hours]
)
```

Keep "Proxy" in the MTBF measure name.

## Visual changes

### Production Performance page

Add one line chart:

- X-axis: `calendar_date`
- Values:
  - `Production Forecast Actual`
  - `Production Forecast`
- Site slicer continues to filter it.

Add a small card:
- `Production Forecast MAPE`

The Stage 12E holdout is the final 60 days of 2025. Label the visual
**Production Forecast — 1-Day-Ahead Holdout**.

Do not call it a 60-day-ahead forecast.

### Energy & Utilities page

Add one line chart:

- X-axis: `calendar_date`
- Values:
  - `Energy Forecast Actual`
  - `Energy Forecast`

Add cards:
- `Energy Forecast MAPE`
- `High Energy Anomaly Rate`
- `High Energy Excess kWh`

Optional supporting chart:
- X-axis: Site
- Value: `High Energy Anomalies`

Label the anomaly content **Contextual Energy Anomalies — 2025**.

### New Reliability & Maintenance page

A sixth page is justified because Stage 13 has enough content to stand alone.

Recommended first-pass layout:

KPI cards:
- Corrective Failures
- Corrective Downtime h
- Weighted MTTR h
- Operating MTBF Proxy h

Monthly line chart:
- X-axis: `calendar_date`
- Value: `Failures per 1000 Operating h`

Bar chart:
- Axis: equipment type
- Value: corrective failures
- source: `vw_monthly_equipment_type_reliability_trend`

Site comparison:
- Axis: site
- Value: `Failures per 1000 Operating h`

Use the existing Velora style and page navigator.

## External benchmark analytics

Do not load the MetroPT or hydraulic-condition outputs into these Velora
operational pages.

They remain portfolio evidence of:

- real-data fault/anomaly detection;
- real-data hydraulic condition classification.

They are not Velora plant sensor results.
