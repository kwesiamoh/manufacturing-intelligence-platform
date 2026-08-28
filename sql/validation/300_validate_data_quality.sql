\pset pager off

\echo '=== Stage 7A active core rule count ==='
SELECT COUNT(*) AS rule_count
FROM dq_rule
WHERE active_flag = TRUE
  AND LEFT(rule_code, 8) <> 'METROPT_';

\echo '=== Stage 7A active core result count ==='
SELECT COUNT(*) AS result_count
FROM dq_rule r
JOIN vw_data_quality_latest l ON l.rule_code = r.rule_code
WHERE r.active_flag = TRUE
  AND LEFT(r.rule_code, 8) <> 'METROPT_';

\echo '=== Failed active core rules: expected zero ==='
SELECT COUNT(*) AS failed_rules
FROM dq_rule r
JOIN vw_data_quality_latest l ON l.rule_code = r.rule_code
WHERE r.active_flag = TRUE
  AND LEFT(r.rule_code, 8) <> 'METROPT_'
  AND l.result_status = 'FAIL';

\echo '=== Domain DQ summary ==='
SELECT
    domain_name,
    rule_count,
    passed_rules,
    failed_rules,
    evaluated_rows,
    failed_rows,
    ROUND((weighted_data_quality_score*100)::numeric,4) AS dq_score_pct
FROM vw_data_quality_summary
ORDER BY domain_name;

\echo '=== Enterprise DQ summary ==='
SELECT
    rule_count,
    passed_rules,
    failed_rules,
    evaluated_rows,
    failed_rows,
    ROUND((weighted_data_quality_score*100)::numeric,4) AS dq_score_pct
FROM vw_data_quality_enterprise_summary;

\echo '=== Individual rules ==='
SELECT
    rule_code,
    domain_name,
    severity,
    evaluated_row_count,
    failed_row_count,
    result_status
FROM vw_data_quality_latest
ORDER BY domain_name, rule_code;

\echo '=== Mandatory core DQ gate ==='
DO $validation$
DECLARE
    missing_results bigint;
    failed_results bigint;
BEGIN
    -- METROPT_* rules belong to the optional external benchmark extension.
    -- The canonical Velora gate follows the active core configuration and does
    -- not require or reject optional benchmark WARN results.
    SELECT COUNT(*) INTO missing_results
    FROM dq_rule r
    LEFT JOIN vw_data_quality_latest l ON l.rule_code = r.rule_code
    WHERE r.active_flag = TRUE
      AND LEFT(r.rule_code, 8) <> 'METROPT_'
      AND l.rule_code IS NULL;

    SELECT COUNT(*) INTO failed_results
    FROM dq_rule r
    JOIN vw_data_quality_latest l ON l.rule_code = r.rule_code
    WHERE r.active_flag = TRUE
      AND LEFT(r.rule_code, 8) <> 'METROPT_'
      AND l.result_status = 'FAIL';

    IF missing_results <> 0 THEN
        RAISE EXCEPTION 'Core DQ gate has % active rules without results', missing_results;
    END IF;
    IF failed_results <> 0 THEN
        RAISE EXCEPTION 'Core DQ gate has % mandatory FAIL results', failed_results;
    END IF;
END
$validation$;
