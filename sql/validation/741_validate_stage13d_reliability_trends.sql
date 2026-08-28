-- Stage 13D validation
\pset pager off

\echo '=== 1. Monthly trend coverage ==='
SELECT
    MIN(month_start) AS min_month,
    MAX(month_start) AS max_month,
    COUNT(DISTINCT month_start) AS months,
    COUNT(DISTINCT site_code) AS sites,
    COUNT(DISTINCT line_code) AS lines,
    COUNT(*) AS site_line_month_rows
FROM analytics.vw_monthly_reliability_trend;

\echo ''
\echo '=== 2. Failure reconciliation ==='
SELECT
    SUM(corrective_failure_count) AS corrective_failures,
    ROUND(SUM(corrective_downtime_hours)::numeric,2)
        AS corrective_downtime_hours
FROM analytics.vw_monthly_reliability_trend;

\echo ''
\echo '=== 3. Trend KPI sanity ==='
SELECT
    COUNT(*) FILTER (
        WHERE corrective_failures_per_1000_operating_hours < 0
    ) AS invalid_failure_rate,
    COUNT(*) FILTER (
        WHERE monthly_operating_hours_mtbf_proxy <= 0
    ) AS invalid_mtbf_proxy,
    COUNT(*) FILTER (
        WHERE mttr_hours <= 0
    ) AS invalid_mttr,
    COUNT(*) FILTER (
        WHERE corrective_downtime_to_operating_time_ratio < 0
    ) AS invalid_downtime_ratio
FROM analytics.vw_monthly_reliability_trend;

\echo ''
\echo '=== 4. Enterprise monthly reliability trend ==='
SELECT
    month_start,
    SUM(corrective_failure_count) AS corrective_failures,
    ROUND(SUM(corrective_downtime_hours)::numeric,2)
        AS corrective_downtime_h,
    ROUND(
        (
            SUM(corrective_failure_count) * 1000.0
            / NULLIF(SUM(line_operating_hours),0)
        )::numeric,
        3
    ) AS failures_per_1000_operating_h,
    ROUND(
        (
            SUM(line_operating_hours)
            / NULLIF(SUM(corrective_failure_count),0)
        )::numeric,
        2
    ) AS operating_mtbf_proxy_h,
    ROUND(
        (
            SUM(corrective_downtime_hours)
            / NULLIF(SUM(line_operating_hours),0)
        )::numeric,
        5
    ) AS downtime_to_operating_ratio
FROM analytics.vw_monthly_reliability_trend
GROUP BY month_start
ORDER BY month_start;

\echo ''
\echo '=== 5. Site trend summary ==='
SELECT
    site_code,
    SUM(corrective_failure_count) AS corrective_failures,
    ROUND(SUM(corrective_downtime_hours)::numeric,2) AS downtime_h,
    ROUND(
        (
            SUM(corrective_failure_count) * 1000.0
            / NULLIF(SUM(line_operating_hours),0)
        )::numeric,
        3
    ) AS failures_per_1000_operating_h,
    ROUND(
        (
            SUM(line_operating_hours)
            / NULLIF(SUM(corrective_failure_count),0)
        )::numeric,
        2
    ) AS operating_mtbf_proxy_h
FROM analytics.vw_monthly_reliability_trend
GROUP BY site_code
ORDER BY failures_per_1000_operating_h DESC;

\echo ''
\echo '=== 6. Equipment-type monthly trend leaders ==='
SELECT
    month_start,
    equipment_type,
    SUM(corrective_failure_count) AS corrective_failures,
    ROUND(SUM(corrective_downtime_hours)::numeric,2) AS downtime_h,
    ROUND(AVG(mttr_hours)::numeric,4) AS avg_mttr_h
FROM analytics.vw_monthly_equipment_type_reliability_trend
GROUP BY month_start, equipment_type
ORDER BY month_start, corrective_failures DESC;

\echo ''
\echo '=== Stage 13D validation complete ==='
