CREATE OR REPLACE VIEW vw_data_quality_latest AS
SELECT
    r.rule_code,
    r.rule_name,
    r.domain_name,
    r.target_object,
    r.rule_type,
    r.severity,
    x.run_timestamp,
    x.evaluated_row_count,
    x.failed_row_count,
    x.failure_rate,
    x.result_status,
    x.result_detail
FROM dq_result x
JOIN dq_rule r ON r.dq_rule_id=x.dq_rule_id;


CREATE OR REPLACE VIEW vw_data_quality_summary AS
SELECT
    domain_name,
    COUNT(*) AS rule_count,
    COUNT(*) FILTER (WHERE result_status='PASS') AS passed_rules,
    COUNT(*) FILTER (WHERE result_status='FAIL') AS failed_rules,
    SUM(evaluated_row_count) AS evaluated_rows,
    SUM(failed_row_count) AS failed_rows,
    CASE
        WHEN SUM(evaluated_row_count)>0
        THEN 1.0 - SUM(failed_row_count)::numeric/SUM(evaluated_row_count)
    END AS weighted_data_quality_score
FROM vw_data_quality_latest
GROUP BY domain_name;


CREATE OR REPLACE VIEW vw_data_quality_enterprise_summary AS
SELECT
    COUNT(*) AS rule_count,
    COUNT(*) FILTER (WHERE result_status='PASS') AS passed_rules,
    COUNT(*) FILTER (WHERE result_status='FAIL') AS failed_rules,
    SUM(evaluated_row_count) AS evaluated_rows,
    SUM(failed_row_count) AS failed_rows,
    CASE
        WHEN SUM(evaluated_row_count)>0
        THEN 1.0 - SUM(failed_row_count)::numeric/SUM(evaluated_row_count)
    END AS weighted_data_quality_score
FROM vw_data_quality_latest;
