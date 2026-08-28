-- Stage 12B.2 validation: Laney p' chart
\pset pager off

-- The accepted Laney view is a nested analytical view. Materialize it once for
-- this validation session so each diagnostic and mandatory gate evaluates the
-- same accepted snapshot without repeatedly expanding the full view chain.
CREATE TEMP TABLE laney_pprime_validation_snapshot AS
SELECT *
FROM analytics.vw_quality_reject_laney_pprime;

ANALYZE laney_pprime_validation_snapshot;

\echo '=== 1. View row count and phase coverage ==='
SELECT
    COUNT(*) AS row_count,
    MIN(timestamp_start) AS min_timestamp,
    MAX(timestamp_start) AS max_timestamp,
    COUNT(*) FILTER (WHERE spc_phase = 'BASELINE_2024') AS baseline_rows,
    COUNT(*) FILTER (WHERE spc_phase = 'MONITORING_2025') AS monitoring_rows
FROM laney_pprime_validation_snapshot;

\echo ''
\echo '=== 2. Sigma-z / dispersion summary across site-line-product baselines ==='
SELECT
    COUNT(*) AS combinations,
    ROUND(MIN(sigma_z)::numeric, 3) AS min_sigma_z,
    ROUND(AVG(sigma_z)::numeric, 3) AS avg_sigma_z,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sigma_z)::numeric, 3) AS median_sigma_z,
    ROUND(MAX(sigma_z)::numeric, 3) AS max_sigma_z,
    COUNT(*) FILTER (WHERE sigma_z > 1.0) AS overdispersed_combinations
FROM (
    SELECT DISTINCT
        site_code, line_code, product_code, sigma_z
    FROM laney_pprime_validation_snapshot
) x;

\echo ''
\echo '=== 3. Laney control-status distribution ==='
SELECT
    spc_phase,
    control_status,
    COUNT(*) AS rows,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY spc_phase),
        4
    ) AS pct_of_phase
FROM laney_pprime_validation_snapshot
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
FROM laney_pprime_validation_snapshot
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
    ROUND(sigma_z::numeric, 3) AS sigma_z,
    ROUND(laney_standardized_z::numeric, 3) AS laney_z
FROM laney_pprime_validation_snapshot
WHERE spc_phase = 'MONITORING_2025'
  AND control_status = 'ABOVE_UCL'
ORDER BY laney_standardized_z DESC NULLS LAST
LIMIT 20;

\echo ''
\echo '=== 6. Comparison with ordinary p-chart ==='
SELECT (to_regclass('analytics.vw_quality_reject_pchart') IS NOT NULL)::text
    AS ordinary_pchart_available
\gset

\if :ordinary_pchart_available
SELECT
    p.spc_phase,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE p.is_special_cause)
        / COUNT(*),
        4
    ) AS ordinary_pchart_special_cause_pct,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE l.is_special_cause)
        / COUNT(*),
        4
    ) AS laney_pprime_special_cause_pct
FROM analytics.vw_quality_reject_pchart p
JOIN laney_pprime_validation_snapshot l
  ON l.production_id = p.production_id
GROUP BY p.spc_phase
ORDER BY p.spc_phase;
\else
\echo 'Optional ordinary p-chart view is absent; comparison is not part of the canonical Laney gate.'
\endif

\echo ''
\echo '=== 7. Sanity checks ==='
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
    COUNT(*) FILTER (WHERE sigma_z IS NULL OR sigma_z <= 0) AS invalid_sigma_z,
    COUNT(*) FILTER (
        WHERE abs(subgroup_units - round(subgroup_units)) > 0.000001
           OR abs(reject_units - round(reject_units)) > 0.000001
    ) AS noninteger_count_rows
FROM laney_pprime_validation_snapshot;

\echo ''
\echo '=== 8. Provenance ==='
SELECT DISTINCT
    source_code,
    is_real_data,
    provenance_note
FROM laney_pprime_validation_snapshot;

\echo ''
\echo '=== Stage 12B.2 Laney p-prime validation complete ==='

\echo '=== Mandatory Stage 12B.2 gate ==='
DO $validation$
DECLARE
    bad_count bigint;
BEGIN
    IF (SELECT COUNT(*) FROM laney_pprime_validation_snapshot) <> 65790
       OR (SELECT COUNT(*) FROM laney_pprime_validation_snapshot
           WHERE spc_phase = 'BASELINE_2024') <> 32940
       OR (SELECT COUNT(*) FROM laney_pprime_validation_snapshot
           WHERE spc_phase = 'MONITORING_2025') <> 32850 THEN
        RAISE EXCEPTION 'Stage 12B.2 Laney p-prime view has incomplete canonical phase coverage';
    END IF;

    SELECT COUNT(*) INTO bad_count
    FROM laney_pprime_validation_snapshot
    WHERE subgroup_units <= 0 OR reject_units < 0 OR reject_units > subgroup_units
       OR reject_proportion < 0 OR reject_proportion > 1
       OR lower_control_limit < 0 OR upper_control_limit > 1
       OR lower_control_limit > center_line OR center_line > upper_control_limit
       OR sigma_z IS NULL OR sigma_z <= 0
       OR abs(subgroup_units - round(subgroup_units)) > 0.000001
       OR abs(reject_units - round(reject_units)) > 0.000001;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'Stage 12B.2 Laney p-prime gate found % invalid rows', bad_count;
    END IF;

    IF EXISTS (
        SELECT 1 FROM laney_pprime_validation_snapshot
        WHERE source_code <> 'SYNTHETIC_ENTERPRISE' OR is_real_data IS DISTINCT FROM FALSE
    ) THEN
        RAISE EXCEPTION 'Stage 12B.2 provenance gate expected only synthetic Velora integration data';
    END IF;
END
$validation$;
