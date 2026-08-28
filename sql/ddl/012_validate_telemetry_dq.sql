\pset pager off

\echo '=== Stage 7B telemetry rules ==='
SELECT
    rule_code,
    severity,
    evaluated_row_count,
    failed_row_count,
    ROUND((failure_rate*100)::numeric,6) AS finding_rate_pct,
    result_status,
    result_detail
FROM vw_telemetry_data_quality_latest
ORDER BY rule_code;

\echo '=== Structural telemetry failures ==='
SELECT COUNT(*) AS structural_failures
FROM vw_telemetry_data_quality_latest
WHERE result_status='FAIL';

\echo '=== Telemetry warnings ==='
SELECT COUNT(*) AS warning_rules
FROM vw_telemetry_data_quality_latest
WHERE result_status='WARN';

\echo '=== Overall DQ status summary ==='
SELECT *
FROM vw_data_quality_status_summary
ORDER BY domain_name;
