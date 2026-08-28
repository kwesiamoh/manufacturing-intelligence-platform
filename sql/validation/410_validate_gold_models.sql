\pset pager off

\echo '=== Gold model Gold model row counts ==='
SELECT 'gold.vw_shift_manufacturing_performance' AS object_name, COUNT(*) AS row_count
FROM gold.vw_shift_manufacturing_performance
UNION ALL
SELECT 'gold.vw_line_daily_performance', COUNT(*)
FROM gold.vw_line_daily_performance
UNION ALL
SELECT 'gold.vw_site_daily_performance', COUNT(*)
FROM gold.vw_site_daily_performance
UNION ALL
SELECT 'gold.vw_site_executive_summary', COUNT(*)
FROM gold.vw_site_executive_summary
UNION ALL
SELECT 'gold.vw_data_quality_domain_summary', COUNT(*)
FROM gold.vw_data_quality_domain_summary
UNION ALL
SELECT 'gold.vw_data_quality_rule_status', COUNT(*)
FROM gold.vw_data_quality_rule_status
ORDER BY object_name;

\echo ''
\echo '=== Expected row counts ==='
SELECT
    (SELECT COUNT(*) FROM gold.vw_shift_manufacturing_performance) = 65790 AS shift_rows_ok,
    (SELECT COUNT(*) FROM gold.vw_line_daily_performance) = 21930 AS line_daily_rows_ok,
    (SELECT COUNT(*) FROM gold.vw_site_daily_performance) = 4386 AS site_daily_rows_ok,
    (SELECT COUNT(*) FROM gold.vw_site_executive_summary) = 6 AS site_summary_rows_ok,
    NOT EXISTS (
        SELECT 1
        FROM dq_rule r
        LEFT JOIN gold.vw_data_quality_rule_status g ON g.rule_code = r.rule_code
        WHERE r.active_flag = TRUE
          AND LEFT(r.rule_code, 8) <> 'METROPT_'
          AND g.rule_code IS NULL
    ) AS active_core_dq_rules_present,
    NOT EXISTS (
        SELECT DISTINCT r.domain_name
        FROM dq_rule r
        WHERE r.active_flag = TRUE
          AND LEFT(r.rule_code, 8) <> 'METROPT_'
        EXCEPT
        SELECT domain_name FROM gold.vw_data_quality_domain_summary
    ) AS active_core_dq_domains_present;

\echo ''
\echo '=== Shift join uniqueness: expected zero ==='
SELECT COUNT(*) AS duplicate_production_record_ids
FROM (
    SELECT production_record_id
    FROM gold.vw_shift_manufacturing_performance
    GROUP BY production_record_id
    HAVING COUNT(*) <> 1
) x;

\echo ''
\echo '=== Line-day join uniqueness: expected zero ==='
SELECT COUNT(*) AS duplicate_line_days
FROM (
    SELECT date_id, site_code, line_code
    FROM gold.vw_line_daily_performance
    GROUP BY date_id, site_code, line_code
    HAVING COUNT(*) <> 1
) x;

\echo ''
\echo '=== Site-day join uniqueness: expected zero ==='
SELECT COUNT(*) AS duplicate_site_days
FROM (
    SELECT date_id, site_code
    FROM gold.vw_site_daily_performance
    GROUP BY date_id, site_code
    HAVING COUNT(*) <> 1
) x;

\echo ''
\echo '=== Key null checks: expected all zero ==='
SELECT
    COUNT(*) FILTER (WHERE production_record_id IS NULL) AS shift_null_keys,
    COUNT(*) FILTER (WHERE site_code IS NULL) AS shift_null_sites,
    COUNT(*) FILTER (WHERE line_code IS NULL) AS shift_null_lines
FROM gold.vw_shift_manufacturing_performance;

SELECT
    COUNT(*) FILTER (WHERE date_id IS NULL) AS line_day_null_dates,
    COUNT(*) FILTER (WHERE site_code IS NULL) AS line_day_null_sites,
    COUNT(*) FILTER (WHERE line_code IS NULL) AS line_day_null_lines
FROM gold.vw_line_daily_performance;

SELECT
    COUNT(*) FILTER (WHERE date_id IS NULL) AS site_day_null_dates,
    COUNT(*) FILTER (WHERE site_code IS NULL) AS site_day_null_sites
FROM gold.vw_site_daily_performance;

\echo ''
\echo '=== Core KPI bounds: expected all zero ==='
SELECT
    COUNT(*) FILTER (WHERE availability < 0 OR availability > 1) AS bad_availability,
    COUNT(*) FILTER (WHERE performance < 0 OR performance > 1) AS bad_performance,
    COUNT(*) FILTER (WHERE quality < 0 OR quality > 1) AS bad_quality,
    COUNT(*) FILTER (WHERE oee < 0 OR oee > 1) AS bad_oee
FROM gold.vw_shift_manufacturing_performance;

\echo ''
\echo '=== Site executive summary ==='
SELECT
    site_code,
    ROUND(avg_line_oee, 4) AS avg_line_oee,
    oee_rank,
    ROUND(total_site_kwh_per_1000_units, 4) AS total_site_kwh_per_1000_units,
    total_site_energy_intensity_rank,
    ROUND(benchmark_electricity_cost_eur_per_1000_units, 4) AS benchmark_eur_per_1000_units,
    cost_intensity_rank,
    ROUND(total_technical_opportunity_eur, 2) AS technical_opportunity_eur
FROM gold.vw_site_executive_summary
ORDER BY oee_rank;

\echo ''
\echo '=== Gold DQ status ==='
SELECT
    domain_name,
    rule_count,
    passed_rules,
    failed_rules,
    failed_rows,
    ROUND(weighted_data_quality_score, 4) AS dq_score_pct
FROM gold.vw_data_quality_domain_summary
ORDER BY domain_name;

\echo ''
\echo '=== Mandatory Gold-model gate ==='
DO $validation$
DECLARE
    bad_count bigint;
BEGIN
    IF (SELECT COUNT(*) FROM gold.vw_shift_manufacturing_performance) <> 65790
       OR (SELECT COUNT(*) FROM gold.vw_line_daily_performance) <> 21930
       OR (SELECT COUNT(*) FROM gold.vw_site_daily_performance) <> 4386
       OR (SELECT COUNT(*) FROM gold.vw_site_executive_summary) <> 6 THEN
        RAISE EXCEPTION 'Gold operational view row counts do not match the canonical population';
    END IF;

    SELECT SUM(n) INTO bad_count
    FROM (
        SELECT COUNT(*) AS n FROM (
            SELECT production_record_id
            FROM gold.vw_shift_manufacturing_performance
            GROUP BY production_record_id HAVING COUNT(*) <> 1
        ) x
        UNION ALL SELECT COUNT(*) FROM (
            SELECT date_id, site_code, line_code
            FROM gold.vw_line_daily_performance
            GROUP BY date_id, site_code, line_code HAVING COUNT(*) <> 1
        ) x
        UNION ALL SELECT COUNT(*) FROM (
            SELECT date_id, site_code
            FROM gold.vw_site_daily_performance
            GROUP BY date_id, site_code HAVING COUNT(*) <> 1
        ) x
        UNION ALL SELECT COUNT(*) FROM gold.vw_shift_manufacturing_performance
        WHERE production_record_id IS NULL OR site_code IS NULL OR line_code IS NULL
           OR availability < 0 OR availability > 1
           OR performance < 0 OR performance > 1
           OR quality < 0 OR quality > 1 OR oee < 0 OR oee > 1
        UNION ALL SELECT COUNT(*) FROM gold.vw_line_daily_performance
        WHERE date_id IS NULL OR site_code IS NULL OR line_code IS NULL
        UNION ALL SELECT COUNT(*) FROM gold.vw_site_daily_performance
        WHERE date_id IS NULL OR site_code IS NULL
    ) gold_checks;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'Gold operational integrity gate found % invalid rows or key groups', bad_count;
    END IF;

    -- Validate the active Velora/core DQ configuration dynamically. Optional
    -- METROPT_* benchmark rules may be configured and/or executed, but are not
    -- required inputs to this operational build.
    SELECT COUNT(*) INTO bad_count
    FROM dq_rule r
    LEFT JOIN gold.vw_data_quality_rule_status g ON g.rule_code = r.rule_code
    WHERE r.active_flag = TRUE
      AND LEFT(r.rule_code, 8) <> 'METROPT_'
      AND (g.rule_code IS NULL OR g.result_status = 'FAIL');
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'Gold DQ gate has % active core rules missing or in FAIL status', bad_count;
    END IF;

    SELECT COUNT(*) INTO bad_count
    FROM (
        SELECT DISTINCT r.domain_name
        FROM dq_rule r
        WHERE r.active_flag = TRUE
          AND LEFT(r.rule_code, 8) <> 'METROPT_'
        EXCEPT
        SELECT domain_name FROM gold.vw_data_quality_domain_summary
    ) missing_domains;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'Gold DQ domain summary is missing % active core domains', bad_count;
    END IF;
END
$validation$;
