-- Reliability & Maintenance reporting views for the governed MetroPT-informed
-- compressor predictive-maintenance scenario.

CREATE SCHEMA IF NOT EXISTS gold;

CREATE OR REPLACE VIEW gold.vw_compressor_predictive_maintenance_detail AS
SELECT
    w.scenario_scope,
    s.site_id,
    s.site_code,
    s.site_name,
    e.equipment_id,
    e.equipment_code,
    e.equipment_name,
    e.equipment_type,
    w.failure_id,
    w.warning_timestamp,
    w.fault_onset_timestamp,
    w.fault_end_timestamp,
    w.warning_horizon_hours,
    w.warning_lead_time_hours,
    w.warning_outcome,
    w.warning_persistence,
    t.condition_score,
    t.anomaly_score,
    t.condition_state,
    m.work_order_id AS nearest_maintenance_work_order_id,
    m.start_timestamp AS nearest_maintenance_start_timestamp,
    m.maintenance_type AS nearest_maintenance_type,
    src.source_code AS source_dataset,
    w.source_data_origin,
    w.scenario_type,
    w.transformation_basis,
    w.degradation_signal_origin
FROM analytics.metropt_pdm_warning_event w
JOIN public.dim_site s ON s.site_id = w.site_id
JOIN public.dim_equipment e ON e.equipment_id = w.equipment_id
JOIN public.dim_source_dataset src ON src.source_dataset_id = w.source_dataset_id
LEFT JOIN analytics.metropt_enterprise_telemetry t
  ON t.equipment_id = w.equipment_id
 AND t.event_timestamp = w.warning_timestamp
LEFT JOIN LATERAL (
    SELECT
        fm.work_order_id,
        fm.start_timestamp,
        fm.maintenance_type
    FROM public.fact_maintenance fm
    WHERE fm.equipment_id = w.equipment_id
      AND fm.start_timestamp >= w.fault_onset_timestamp
      AND fm.start_timestamp < w.fault_onset_timestamp + INTERVAL '7 days'
    ORDER BY fm.start_timestamp
    LIMIT 1
) m ON TRUE;

CREATE OR REPLACE VIEW gold.vw_compressor_predictive_maintenance_kpi AS
SELECT
    scenario_scope,
    model_name,
    policy_name AS selected_warning_policy,
    evaluation_split,
    warning_horizon_hours AS selected_warning_horizon_hours,
    events_evaluated,
    events_warned,
    events_missed,
    warning_success_rate,
    average_lead_time_hours,
    median_lead_time_hours,
    precision_value AS precision,
    recall_value AS recall,
    false_alerts,
    false_alerts_per_operating_day,
    alert_episodes,
    operating_days
FROM analytics.metropt_pdm_policy_kpi
WHERE is_selected;

CREATE OR REPLACE VIEW gold.vw_compressor_predictive_maintenance_timeline AS
SELECT
    w.failure_id,
    w.scenario_scope,

    s.site_id,
    s.site_code,
    s.site_name,

    e.equipment_id,
    e.equipment_code,
    e.equipment_name,
    e.equipment_type,

    t.event_timestamp,
    t.source_event_timestamp,

    EXTRACT(
        EPOCH FROM (w.fault_onset_timestamp - t.event_timestamp)
    ) / 3600.0 AS hours_to_fault,

    w.warning_timestamp,
    w.fault_onset_timestamp,
    w.fault_end_timestamp,
    w.warning_horizon_hours,
    w.warning_lead_time_hours,
    w.warning_outcome,

    CASE
        WHEN t.event_timestamp < w.warning_timestamp THEN 'BASELINE'
        WHEN t.event_timestamp < w.fault_onset_timestamp THEN 'WARNING'
        ELSE 'FAULT'
    END AS timeline_phase,

    (t.event_timestamp = w.warning_timestamp) AS is_warning_point,
    (t.event_timestamp = w.fault_onset_timestamp) AS is_fault_onset,

    t.selected_warning_state,
    t.fault_state,
    t.condition_state,

    t.condition_score,
    t.degradation_index,
    t.degradation_index * 100.0 AS degradation_pct,
    t.anomaly_score,

    t.reservoir_pressure_bar,
    t.oil_temperature_c,
    t.motor_current_a,
    t.pressure_delta_bar,

    t.reservoir_pressure_slope_60m,
    t.oil_temperature_slope_60m,
    t.motor_current_slope_60m,

    src.source_code AS source_dataset,
    t.source_data_origin,
    t.scenario_type,
    t.transformation_basis,
    t.degradation_signal_origin

FROM analytics.metropt_pdm_warning_event w

JOIN analytics.metropt_enterprise_telemetry t
    ON t.site_id = w.site_id
   AND t.equipment_id = w.equipment_id
   AND t.event_timestamp BETWEEN
       (w.fault_onset_timestamp - INTERVAL '12 hours')
       AND LEAST(
           w.fault_end_timestamp,
           w.fault_onset_timestamp + INTERVAL '30 minutes'
       )

JOIN dim_site s
    ON s.site_id = w.site_id

JOIN dim_equipment e
    ON e.equipment_id = w.equipment_id

JOIN dim_source_dataset src
    ON src.source_dataset_id = w.source_dataset_id

WHERE w.scenario_scope = 'METROPT_INFORMED_SYNTHETIC_ENTERPRISE';


COMMENT ON VIEW gold.vw_compressor_predictive_maintenance_timeline IS
'Event-centred compressor predictive-maintenance timeline exposing twelve hours of pre-fault condition history and thirty minutes of fault context for the governed MetroPT-informed synthetic enterprise scenario.';