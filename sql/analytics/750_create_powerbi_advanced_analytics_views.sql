-- Power BI advanced analytics integration views

CREATE SCHEMA IF NOT EXISTS gold_bi;

DROP VIEW IF EXISTS gold_bi.vw_site_daily_forecast;
DROP VIEW IF EXISTS gold_bi.vw_shift_energy_anomaly;
DROP VIEW IF EXISTS gold_bi.vw_monthly_reliability_trend;
DROP VIEW IF EXISTS gold_bi.vw_monthly_equipment_type_reliability_trend;

CREATE VIEW gold_bi.vw_site_daily_forecast AS
SELECT
    f.calendar_date,
    t.date_id,
    s.site_id,
    f.site_code,
    f.site_name,
    f.forecast_target,
    f.forecast_domain,
    f.actual_value,
    f.ml_forecast_value,
    f.seasonal_naive_value,
    f.selected_forecast_value,
    f.absolute_error,
    -- Compatibility name retained for the existing PBIX. The stored value is
    -- a fractional ratio (for example 0.0072), not percentage points.
    f.absolute_pct_error AS absolute_pct_error_pct,
    (f.actual_value - f.selected_forecast_value) AS signed_forecast_error
FROM analytics.bi_site_daily_forecast f
LEFT JOIN public.dim_time t
  ON t.calendar_date = f.calendar_date
LEFT JOIN public.dim_site s
  ON s.site_code = f.site_code;

CREATE VIEW gold_bi.vw_shift_energy_anomaly AS
SELECT
    a.production_id,
    a.timestamp_start,
    t.calendar_date,
    a.date_id,
    s.site_id,
    l.line_id,
    a.site_code,
    a.site_name,
    a.line_code,
    a.line_name,
    a.product_code,
    a.product_name,
    a.shift_code,
    a.shift_name,
    a.actual_quantity,
    a.operating_time_min,
    a.line_total_electricity_kwh,
    a.line_idle_electricity_kwh,
    a.idle_energy_share,
    a.expected_kwh,
    a.residual_kwh,
    a.residual_pct,
    a.low_threshold,
    a.high_threshold,
    a.energy_anomaly_status,
    a.is_high_energy_anomaly,
    a.is_low_energy_anomaly
FROM analytics.bi_shift_energy_anomaly a
LEFT JOIN public.dim_time t
  ON t.date_id = a.date_id
LEFT JOIN public.dim_site s
  ON s.site_code = a.site_code
LEFT JOIN public.dim_line l
  ON l.line_code = a.line_code;

CREATE VIEW gold_bi.vw_monthly_reliability_trend AS
SELECT
    r.month_start AS calendar_date,
    t.date_id,
    s.site_id,
    l.line_id,
    r.site_code,
    r.site_name,
    r.line_code,
    r.line_name,
    r.corrective_failure_count,
    r.corrective_downtime_hours::double precision
        AS corrective_downtime_hours,
    r.mttr_hours::double precision AS mttr_hours,
    r.affected_equipment_count,
    r.line_operating_hours::double precision AS line_operating_hours,
    r.planned_production_hours::double precision AS planned_production_hours,
    r.corrective_failures_per_1000_operating_hours::double precision
        AS corrective_failures_per_1000_operating_hours,
    r.monthly_operating_hours_mtbf_proxy::double precision
        AS monthly_operating_hours_mtbf_proxy,
    r.corrective_downtime_to_operating_time_ratio::double precision
        AS corrective_downtime_to_operating_time_ratio
FROM analytics.vw_monthly_reliability_trend r
LEFT JOIN public.dim_time t
  ON t.calendar_date = r.month_start
LEFT JOIN public.dim_site s
  ON s.site_code = r.site_code
LEFT JOIN public.dim_line l
  ON l.line_code = r.line_code;

CREATE VIEW gold_bi.vw_monthly_equipment_type_reliability_trend AS
SELECT
    r.month_start AS calendar_date,
    t.date_id,
    s.site_id,
    r.site_code,
    r.site_name,
    r.equipment_type,
    r.corrective_failure_count,
    r.affected_equipment_count,
    r.corrective_downtime_hours::double precision
        AS corrective_downtime_hours,
    r.mttr_hours::double precision AS mttr_hours,
    r.avg_corrective_downtime_per_failure_hours::double precision
        AS avg_corrective_downtime_per_failure_hours
FROM analytics.vw_monthly_equipment_type_reliability_trend r
LEFT JOIN public.dim_time t
  ON t.calendar_date = r.month_start
LEFT JOIN public.dim_site s
  ON s.site_code = r.site_code;
