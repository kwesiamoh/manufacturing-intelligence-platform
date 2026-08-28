-- Stage 12B validation: quality reject-proportion p-chart
\pset pager off

\echo '=== 1. View row count and date coverage ==='
SELECT
    COUNT(*) AS row_count,
    MIN(timestamp_start) AS min_timestamp,
    MAX(timestamp_start) AS max_timestamp,
    COUNT(*) FILTER (WHERE spc_phase = 'BASELINE_2024') AS baseline_rows,
    COUNT(*) FILTER (WHERE spc_phase = 'MONITORING_2025') AS monitoring_rows
FROM analytics.vw_quality_reject_pchart;

\echo ''
\echo '=== 2. Baseline coverage by line/product ==='
SELECT
    COUNT(DISTINCT (site_code, line_code, product_code)) AS combinations,
    MIN(baseline_subgroup_count) AS min_baseline_subgroups,
    ROUND(AVG(baseline_subgroup_count)::numeric, 2) AS avg_baseline_subgroups,
    MAX(baseline_subgroup_count) AS max_baseline_subgroups,
    COUNT(*) FILTER (WHERE baseline_subgroup_count IS NULL) AS rows_without_baseline
FROM analytics.vw_quality_reject_pchart;

\echo ''
\echo '=== 3. Control-status distribution ==='
SELECT
    spc_phase,
    control_status,
    COUNT(*) AS rows,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY spc_phase),
        4
    ) AS pct_of_phase
FROM analytics.vw_quality_reject_pchart
GROUP BY spc_phase, control_status
ORDER BY spc_phase, control_status;

\echo ''
\echo '=== 4. 2025 special-cause summary by site ==='
SELECT
    site_code,
    site_name,
    COUNT(*) AS monitoring_subgroups,
    COUNT(*) FILTER (WHERE control_status = 'ABOVE_UCL') AS above_ucl,
    COUNT(*) FILTER (WHERE control_status = 'BELOW_LCL') AS below_lcl,
    COUNT(*) FILTER (WHERE control_status = 'IN_CONTROL') AS in_control,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE is_special_cause)
        / NULLIF(COUNT(*), 0),
        4
    ) AS special_cause_pct
FROM analytics.vw_quality_reject_pchart
WHERE spc_phase = 'MONITORING_2025'
GROUP BY site_code, site_name
ORDER BY special_cause_pct DESC, site_code;

\echo ''
\echo '=== 5. Top 20 2025 above-UCL observations ==='
SELECT
    timestamp_start,
    site_code,
    line_code,
    product_code,
    shift_code,
    subgroup_units,
    reject_units,
    ROUND(reject_proportion::numeric, 6) AS reject_proportion,
    ROUND(center_line::numeric, 6) AS center_line,
    ROUND(upper_control_limit::numeric, 6) AS upper_control_limit,
    ROUND(standardized_z::numeric, 3) AS z_score
FROM analytics.vw_quality_reject_pchart
WHERE spc_phase = 'MONITORING_2025'
  AND control_status = 'ABOVE_UCL'
ORDER BY standardized_z DESC NULLS LAST
LIMIT 20;

\echo ''
\echo '=== 6. Sanity checks ==='
SELECT
    COUNT(*) FILTER (WHERE subgroup_units <= 0) AS nonpositive_subgroup_units,
    COUNT(*) FILTER (WHERE reject_units < 0) AS negative_reject_units,
    COUNT(*) FILTER (WHERE reject_units > subgroup_units) AS rejects_gt_units,
    COUNT(*) FILTER (
        WHERE reject_proportion < 0 OR reject_proportion > 1
    ) AS invalid_reject_proportions,
    COUNT(*) FILTER (
        WHERE lower_control_limit < 0 OR upper_control_limit > 1
    ) AS invalid_control_limits,
    COUNT(*) FILTER (
        WHERE lower_control_limit > center_line
           OR center_line > upper_control_limit
    ) AS invalid_limit_order,
    COUNT(*) FILTER (
        WHERE abs(subgroup_units - round(subgroup_units)) > 0.000001
           OR abs(reject_units - round(reject_units)) > 0.000001
    ) AS noninteger_count_rows
FROM analytics.vw_quality_reject_pchart;

\echo ''
\echo '=== 7. Provenance ==='
SELECT DISTINCT
    source_code,
    is_real_data,
    provenance_note
FROM analytics.vw_quality_reject_pchart;

\echo ''
\echo '=== Stage 12B validation complete ==='
