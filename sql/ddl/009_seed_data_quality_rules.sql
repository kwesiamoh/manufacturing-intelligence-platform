INSERT INTO dq_rule
(rule_code, rule_name, domain_name, target_object, rule_type, severity, description)
VALUES
('PROD_REQUIRED_NULLS','Production required fields present','production','fact_production','COMPLETENESS','HIGH','Required production identifiers, quantities, timestamps, and durations must not be null.'),
('PROD_DUP_SOURCE','Production source record unique','production','fact_production','UNIQUENESS','HIGH','Synthetic production source_record_id must be unique within source.'),
('PROD_QTY_RECON','Production quantity reconciliation','production','fact_production','CONSISTENCY','HIGH','Actual quantity must equal good quantity plus reject quantity.'),
('PROD_TIME_VALID','Production time ordering','production','fact_production','VALIDITY','HIGH','End timestamp must be after start; operating time must be within planned production time.'),

('DT_REQUIRED_NULLS','Downtime required fields present','downtime','fact_downtime','COMPLETENESS','HIGH','Required downtime identifiers, timestamps, duration, and lineage fields must not be null.'),
('DT_DUP_SOURCE','Downtime source record unique','downtime','fact_downtime','UNIQUENESS','HIGH','Synthetic downtime source_record_id must be unique within source.'),
('DT_DURATION_RECON','Downtime duration reconciliation','downtime','fact_downtime','CONSISTENCY','HIGH','Stored downtime duration must reconcile with event timestamps.'),
('DT_LINEAGE','Downtime production lineage','downtime','fact_downtime','REFERENTIAL','HIGH','Every synthetic downtime event must link to a production record.'),

('QUALITY_REQUIRED_NULLS','Quality required fields present','quality','fact_quality','COMPLETENESS','HIGH','Required quality identifiers, timestamps, quantities and lineage fields must not be null.'),
('QUALITY_DUP_SOURCE','Quality source record unique','quality','fact_quality','UNIQUENESS','HIGH','Synthetic quality source_record_id must be unique within source.'),
('QUALITY_LINEAGE','Quality production lineage','quality','fact_quality','REFERENTIAL','HIGH','Every synthetic quality event must link to a production record.'),

('MAINT_REQUIRED_NULLS','Maintenance required fields present','maintenance','fact_maintenance','COMPLETENESS','HIGH','Required maintenance identifiers, timestamps, durations, and lineage fields must not be null.'),
('MAINT_DUP_SOURCE','Maintenance source record unique','maintenance','fact_maintenance','UNIQUENESS','HIGH','Synthetic maintenance source_record_id must be unique within source.'),
('MAINT_INTERVAL_VALID','Maintenance interval validity','maintenance','fact_maintenance','VALIDITY','HIGH','Maintenance duration must be positive and reconcile with timestamps.'),
  ('MAINT_LINEAGE','Maintenance downtime lineage','maintenance','fact_maintenance','REFERENTIAL','HIGH','Every synthetic maintenance work order must link to a source-qualified downtime event.'),

('ENERGY_REQUIRED_NULLS','Energy required fields present','energy','fact_energy','COMPLETENESS','HIGH','Required energy identifiers, timestamps, consumption and lineage fields must not be null.'),
('ENERGY_DUP_SOURCE','Energy source record unique','energy','fact_energy','UNIQUENESS','HIGH','Synthetic energy source_record_id must be unique within source.'),
('ENERGY_POSITIVE','Energy values positive','energy','fact_energy','VALIDITY','HIGH','Synthetic electricity consumption and demand must be positive.'),
('ENERGY_LINEAGE','Energy production lineage','energy','fact_energy','REFERENTIAL','HIGH','Every synthetic line-energy record must link to a production record.'),

('SITE_ENERGY_RECON','Site energy reconciliation','energy','fact_site_energy_detail','CONSISTENCY','HIGH','Site total electricity must equal line electricity plus site auxiliary electricity.'),
('LINE_ENERGY_RECON','Line energy reconciliation','energy','fact_line_energy_detail','CONSISTENCY','HIGH','Line total electricity must equal production plus idle electricity.'),
('AUX_ENERGY_RECON','Auxiliary energy reconciliation','energy','fact_site_energy_detail','CONSISTENCY','HIGH','Auxiliary electricity must equal auxiliary kW multiplied by shift hours.'),

('EUROSTAT_PRICE_COVERAGE','Eurostat benchmark price coverage','external_benchmark','ref_eurostat_electricity_price_observation','COMPLETENESS','MEDIUM','Six target countries must have four semester benchmark prices for 2024-2025.'),
('EUROSTAT_PRICE_POSITIVE','Eurostat benchmark prices positive','external_benchmark','ref_eurostat_electricity_price_observation','VALIDITY','HIGH','Selected EUR/kWh benchmark price observations must be positive.'),

('TELEMETRY_REQUIRED_FIELDS_COMPLETE','Telemetry required fields present','telemetry','analytics.metropt_enterprise_telemetry','COMPLETENESS','HIGH','Required enterprise telemetry reporting, integration, condition, and lineage fields must not be null.'),
('TELEMETRY_EQUIPMENT_TIMESTAMP_UNIQUE','Telemetry equipment timestamp unique','telemetry','analytics.metropt_enterprise_telemetry','UNIQUENESS','HIGH','Each governed enterprise equipment and event timestamp pair must be unique.'),
('TELEMETRY_ENTERPRISE_MAPPING_VALID','Telemetry enterprise mapping valid','telemetry','analytics.metropt_enterprise_telemetry','REFERENTIAL','HIGH','Each telemetry row must resolve to its governed site and compressed-air equipment mapping.'),
('TELEMETRY_LINEAGE_VALID','Telemetry lineage valid','telemetry','analytics.metropt_enterprise_telemetry','LINEAGE','HIGH','Each enterprise telemetry row must retain the governed external-source and synthetic-scenario lineage.'),
('TELEMETRY_CADENCE_CONTINUITY','Telemetry cadence continuity','telemetry','analytics.metropt_enterprise_telemetry','TIMELINESS','MEDIUM','Consecutive observations should follow the source-supported five-minute cadence; retained source availability and non-operating gaps are reported as WARN rather than fabricated.')
ON CONFLICT (rule_code) DO UPDATE SET
    rule_name=EXCLUDED.rule_name,
    domain_name=EXCLUDED.domain_name,
    target_object=EXCLUDED.target_object,
    rule_type=EXCLUDED.rule_type,
    severity=EXCLUDED.severity,
    description=EXCLUDED.description,
    active_flag=TRUE;
