CREATE OR REPLACE VIEW vw_telemetry_data_quality_latest AS
SELECT
    r.rule_code,
    r.rule_name,
    r.rule_type,
    r.severity,
    x.run_timestamp,
    x.evaluated_row_count,
    x.failed_row_count,
    x.failure_rate,
    x.result_status,
    x.result_detail
FROM dq_result x
JOIN dq_rule r
  ON r.dq_rule_id=x.dq_rule_id
WHERE r.domain_name='telemetry';


CREATE OR REPLACE VIEW vw_data_quality_status_summary AS
SELECT
    domain_name,
    COUNT(*) AS rule_count,
    COUNT(*) FILTER (WHERE result_status='PASS') AS passed_rules,
    COUNT(*) FILTER (WHERE result_status='WARN') AS warning_rules,
    COUNT(*) FILTER (WHERE result_status='FAIL') AS failed_rules
FROM vw_data_quality_latest
GROUP BY domain_name;
