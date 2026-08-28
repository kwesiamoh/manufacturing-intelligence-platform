-- Stage 7B — MetroPT telemetry-specific DQ rules

INSERT INTO dq_rule
(rule_code, rule_name, domain_name, target_object, rule_type, severity, description)
VALUES
('METROPT_TIMESTAMP_NULL','MetroPT timestamps present','telemetry','MetroPT-3 Silver','COMPLETENESS','HIGH','Timestamp must be present for every telemetry row.'),
('METROPT_TIMESTAMP_DUP','MetroPT timestamps unique','telemetry','MetroPT-3 Silver','UNIQUENESS','HIGH','Duplicate telemetry timestamps are not expected.'),
('METROPT_INTERVAL_GAP','MetroPT cadence gaps','telemetry','MetroPT-3 Silver','TIMELINESS','MEDIUM','Detect intervals materially larger than the dataset median sampling interval.'),
('METROPT_SENSOR_NULL','MetroPT sensor values present','telemetry','MetroPT-3 Silver','COMPLETENESS','MEDIUM','Count missing numeric sensor values.'),
('METROPT_SENSOR_FROZEN','MetroPT frozen continuous signals','telemetry','MetroPT-3 Silver','VALIDITY','MEDIUM','Detect unusually long unchanged runs in continuous analog sensors.'),
('METROPT_SENSOR_SPIKE','MetroPT abrupt signal changes','telemetry','MetroPT-3 Silver','VALIDITY','MEDIUM','Detect extreme first-difference changes using a robust MAD rule.')
ON CONFLICT (rule_code) DO UPDATE SET
    rule_name=EXCLUDED.rule_name,
    domain_name=EXCLUDED.domain_name,
    target_object=EXCLUDED.target_object,
    rule_type=EXCLUDED.rule_type,
    severity=EXCLUDED.severity,
    description=EXCLUDED.description,
    active_flag=TRUE;
