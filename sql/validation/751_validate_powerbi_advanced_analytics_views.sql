\pset pager off

\echo '=== 1. Forecast integration ==='
SELECT
    COUNT(*) AS rows,
    COUNT(DISTINCT calendar_date) AS dates,
    COUNT(DISTINCT site_code) AS sites,
    forecast_domain,
    MIN(calendar_date) AS min_date,
    MAX(calendar_date) AS max_date
FROM gold_bi.vw_site_daily_forecast
GROUP BY forecast_domain
ORDER BY forecast_domain;

\echo ''
\echo '=== 1a. Forecast target/domain mapping and landing grain ==='
SELECT forecast_target, forecast_domain, COUNT(*) AS rows
FROM analytics.bi_site_daily_forecast
GROUP BY forecast_target, forecast_domain
ORDER BY forecast_domain;

SELECT COUNT(*) AS duplicate_date_site_domain_rows
FROM (
    SELECT calendar_date, site_code, forecast_domain
    FROM analytics.bi_site_daily_forecast
    GROUP BY calendar_date, site_code, forecast_domain
    HAVING COUNT(*) <> 1
) duplicates;

\echo ''
\echo '=== 2. Forecast dimension-key coverage ==='
SELECT
    COUNT(*) FILTER (WHERE date_id IS NULL) AS missing_date_id,
    COUNT(*) FILTER (WHERE site_id IS NULL) AS missing_site_id
FROM gold_bi.vw_site_daily_forecast;

\echo ''
\echo '=== 3. Energy anomaly integration ==='
SELECT
    COUNT(*) AS monitored_shifts,
    COUNT(*) FILTER (WHERE is_high_energy_anomaly) AS high_energy_anomalies,
    COUNT(*) FILTER (WHERE is_low_energy_anomaly) AS low_energy_anomalies,
    ROUND(SUM(
        CASE WHEN is_high_energy_anomaly
             THEN residual_kwh ELSE 0 END
    )::numeric, 2) AS high_energy_excess_kwh,
    MIN(calendar_date) AS min_date,
    MAX(calendar_date) AS max_date
FROM gold_bi.vw_shift_energy_anomaly;

\echo ''
\echo '=== 3a. Energy-anomaly landing grain and status consistency ==='
SELECT
    COUNT(*) FILTER (
        WHERE is_high_energy_anomaly <> (energy_anomaly_status = 'HIGH_ENERGY')
           OR is_low_energy_anomaly <> (energy_anomaly_status = 'LOW_ENERGY')
    ) AS inconsistent_status_flags,
    COUNT(*) - COUNT(DISTINCT production_id) AS duplicate_production_ids
FROM analytics.bi_shift_energy_anomaly;

\echo ''
\echo '=== 4. Energy anomaly dimension-key coverage ==='
SELECT
    COUNT(*) FILTER (WHERE calendar_date IS NULL) AS missing_calendar_date,
    COUNT(*) FILTER (WHERE site_id IS NULL) AS missing_site_id,
    COUNT(*) FILTER (WHERE line_id IS NULL) AS missing_line_id
FROM gold_bi.vw_shift_energy_anomaly;

\echo ''
\echo '=== 5. Reliability trend integration ==='
SELECT
    COUNT(*) AS rows,
    COUNT(DISTINCT calendar_date) AS months,
    COUNT(DISTINCT site_code) AS sites,
    COUNT(DISTINCT line_code) AS lines,
    SUM(corrective_failure_count) AS corrective_failures,
    ROUND(SUM(corrective_downtime_hours)::numeric, 2)
        AS corrective_downtime_h,
    MIN(calendar_date) AS min_month,
    MAX(calendar_date) AS max_month
FROM gold_bi.vw_monthly_reliability_trend;

\echo ''
\echo '=== 5a. Reliability accepted downtime reconciliation ==='
SELECT
    ROUND(SUM(corrective_downtime_hours)::numeric, 6) AS observed_hours,
    14856.65::numeric AS expected_hours,
    0.01::numeric AS tolerance_hours
FROM gold_bi.vw_monthly_reliability_trend;

\echo ''
\echo '=== 6. Reliability dimension-key coverage ==='
SELECT
    COUNT(*) FILTER (WHERE date_id IS NULL) AS missing_date_id,
    COUNT(*) FILTER (WHERE site_id IS NULL) AS missing_site_id,
    COUNT(*) FILTER (WHERE line_id IS NULL) AS missing_line_id
FROM gold_bi.vw_monthly_reliability_trend;

\echo ''
\echo '=== 7. Latest successful bridge load provenance ==='
SELECT
    load_id,
    loaded_at,
    loader_version,
    forecast_sha256,
    anomaly_sha256,
    forecast_row_count,
    anomaly_row_count,
    reliability_row_count
FROM analytics.bi_advanced_analytics_load_audit
ORDER BY load_id DESC
LIMIT 1;

\echo ''
\echo '=== Power BI advanced-analytics integration validation complete ==='

\echo '=== Mandatory Power BI advanced-analytics gate ==='
DO $validation$
DECLARE
    bad_count bigint;
BEGIN
    IF (SELECT COUNT(*) FROM gold_bi.vw_site_daily_forecast) <> 720
       OR (SELECT COUNT(DISTINCT calendar_date) FROM gold_bi.vw_site_daily_forecast) <> 60
       OR (SELECT COUNT(DISTINCT site_code) FROM gold_bi.vw_site_daily_forecast) <> 6
       OR (SELECT COUNT(DISTINCT forecast_domain) FROM gold_bi.vw_site_daily_forecast) <> 2
       OR EXISTS (
            SELECT 1 FROM gold_bi.vw_site_daily_forecast
            GROUP BY forecast_domain
            HAVING COUNT(*) <> 360
                OR COUNT(DISTINCT calendar_date) <> 60
                OR MIN(calendar_date) <> DATE '2025-11-02'
                OR MAX(calendar_date) <> DATE '2025-12-31'
       ) THEN
        RAISE EXCEPTION 'Power BI forecast bridge does not match the accepted 720-row holdout';
    END IF;

    IF EXISTS (
        SELECT 1 FROM analytics.bi_site_daily_forecast
        WHERE forecast_domain NOT IN ('PRODUCTION', 'ENERGY')
           OR (forecast_target = 'daily_actual_quantity'
               AND forecast_domain <> 'PRODUCTION')
           OR (forecast_target = 'daily_site_total_electricity_kwh'
               AND forecast_domain <> 'ENERGY')
           OR forecast_target NOT IN (
                'daily_actual_quantity',
                'daily_site_total_electricity_kwh'
           )
    ) OR EXISTS (
        SELECT 1
        FROM analytics.bi_site_daily_forecast
        GROUP BY calendar_date, site_code, forecast_domain
        HAVING COUNT(*) <> 1
    ) THEN
        RAISE EXCEPTION 'Power BI forecast target mapping or Date+Site+Domain grain is invalid';
    END IF;

    SELECT COUNT(*) INTO bad_count
    FROM gold_bi.vw_site_daily_forecast
    WHERE date_id IS NULL OR site_id IS NULL;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'Power BI forecast bridge has % rows with missing dimension keys', bad_count;
    END IF;

    IF (SELECT COUNT(*) FROM gold_bi.vw_shift_energy_anomaly) <> 32850
       OR (SELECT COUNT(*) FROM gold_bi.vw_shift_energy_anomaly
           WHERE is_high_energy_anomaly) <> 254
       OR (SELECT COUNT(*) FROM gold_bi.vw_shift_energy_anomaly
           WHERE is_low_energy_anomaly) <> 282
       OR (SELECT MIN(calendar_date) FROM gold_bi.vw_shift_energy_anomaly) <> DATE '2025-01-01'
       OR (SELECT MAX(calendar_date) FROM gold_bi.vw_shift_energy_anomaly) <> DATE '2025-12-31' THEN
        RAISE EXCEPTION 'Power BI energy-anomaly bridge does not match the accepted monitoring output';
    END IF;
    SELECT COUNT(*) INTO bad_count
    FROM gold_bi.vw_shift_energy_anomaly
    WHERE calendar_date IS NULL OR site_id IS NULL OR line_id IS NULL;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'Power BI energy-anomaly bridge has % rows with missing dimension keys', bad_count;
    END IF;

    IF EXISTS (
        SELECT 1 FROM analytics.bi_shift_energy_anomaly
        WHERE energy_anomaly_status NOT IN ('NORMAL', 'HIGH_ENERGY', 'LOW_ENERGY')
           OR is_high_energy_anomaly <> (energy_anomaly_status = 'HIGH_ENERGY')
           OR is_low_energy_anomaly <> (energy_anomaly_status = 'LOW_ENERGY')
    ) OR EXISTS (
        SELECT 1 FROM analytics.bi_shift_energy_anomaly
        GROUP BY production_id HAVING COUNT(*) <> 1
    ) OR EXISTS (
        SELECT 1 FROM analytics.bi_shift_energy_anomaly
        GROUP BY date_id, site_code, line_code, shift_code
        HAVING COUNT(*) <> 1
    ) THEN
        RAISE EXCEPTION 'Power BI energy-anomaly status or shift-level grain is invalid';
    END IF;

    IF (SELECT COUNT(*) FROM gold_bi.vw_monthly_reliability_trend) <> 720
       OR (SELECT COUNT(DISTINCT calendar_date) FROM gold_bi.vw_monthly_reliability_trend) <> 24
       OR (SELECT COUNT(DISTINCT site_code) FROM gold_bi.vw_monthly_reliability_trend) <> 6
       OR (SELECT COUNT(DISTINCT line_code) FROM gold_bi.vw_monthly_reliability_trend) <> 30
       OR (SELECT MIN(calendar_date) FROM gold_bi.vw_monthly_reliability_trend) <> DATE '2024-01-01'
       OR (SELECT MAX(calendar_date) FROM gold_bi.vw_monthly_reliability_trend) <> DATE '2025-12-01'
       OR COALESCE((
            SELECT SUM(corrective_failure_count)
            FROM gold_bi.vw_monthly_reliability_trend
       ), 0) <> 46670
       OR ABS(COALESCE((
            SELECT SUM(corrective_downtime_hours)
            FROM gold_bi.vw_monthly_reliability_trend
       ), 0) - 14856.65) > 0.01 THEN
        RAISE EXCEPTION 'Power BI reliability bridge does not match the accepted corrected trend';
    END IF;
    SELECT COUNT(*) INTO bad_count
    FROM gold_bi.vw_monthly_reliability_trend
    WHERE date_id IS NULL OR site_id IS NULL OR line_id IS NULL;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'Power BI reliability bridge has % rows with missing dimension keys', bad_count;
    END IF;

    IF EXISTS (
        SELECT 1 FROM gold_bi.vw_monthly_reliability_trend
        GROUP BY calendar_date, site_code, line_code
        HAVING COUNT(*) <> 1
    ) OR EXISTS (
        SELECT 1 FROM gold_bi.vw_monthly_equipment_type_reliability_trend
        WHERE calendar_date IS NULL OR date_id IS NULL
           OR site_code IS NULL OR site_id IS NULL OR equipment_type IS NULL
    ) OR EXISTS (
        SELECT 1 FROM gold_bi.vw_monthly_equipment_type_reliability_trend
        GROUP BY calendar_date, site_code, equipment_type
        HAVING COUNT(*) <> 1
    ) THEN
        RAISE EXCEPTION 'Power BI reliability key structure is invalid';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM analytics.bi_advanced_analytics_load_audit
        WHERE load_id = (
                SELECT MAX(load_id)
                FROM analytics.bi_advanced_analytics_load_audit
              )
          AND forecast_row_count = 720
          AND anomaly_row_count = 32850
          AND reliability_row_count = 720
          AND forecast_sha256 ~ '^[0-9a-f]{64}$'
          AND anomaly_sha256 ~ '^[0-9a-f]{64}$'
    ) THEN
        RAISE EXCEPTION 'No successful advanced-analytics load audit matches the accepted bridge';
    END IF;
END
$validation$;
