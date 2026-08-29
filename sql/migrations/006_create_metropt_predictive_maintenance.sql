-- Governed MetroPT-informed enterprise predictive-maintenance landing tables.
-- Original MetroPT observations remain external real benchmark data. These
-- tables do not alter fact_maintenance or the accepted reliability KPI chain.

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.metropt_enterprise_telemetry (
    event_timestamp                    TIMESTAMP NOT NULL,
    source_event_timestamp             TIMESTAMP NOT NULL,
    site_id                            INTEGER NOT NULL REFERENCES public.dim_site(site_id),
    equipment_id                       INTEGER NOT NULL REFERENCES public.dim_equipment(equipment_id),
    source_dataset_id                  INTEGER NOT NULL REFERENCES public.dim_source_dataset(source_dataset_id),
    scenario_source_dataset_id         INTEGER NOT NULL REFERENCES public.dim_source_dataset(source_dataset_id),
    tp2_pressure_bar                   DOUBLE PRECISION,
    tp3_pressure_bar                   DOUBLE PRECISION,
    reservoir_pressure_bar             DOUBLE PRECISION,
    oil_temperature_c                  DOUBLE PRECISION,
    motor_current_a                    DOUBLE PRECISION,
    pressure_delta_bar                 DOUBLE PRECISION,
    reservoir_pressure_slope_60m       DOUBLE PRECISION,
    oil_temperature_slope_60m          DOUBLE PRECISION,
    motor_current_slope_60m            DOUBLE PRECISION,
    anomaly_score                      DOUBLE PRECISION,
    degradation_index                  DOUBLE PRECISION NOT NULL CHECK (degradation_index BETWEEN 0 AND 1),
    condition_score                    DOUBLE PRECISION NOT NULL CHECK (condition_score BETWEEN 0 AND 100),
    precursor_failure_id               VARCHAR(64),
    source_fault_event_id              VARCHAR(64),
    fault_state                        BOOLEAN NOT NULL,
    condition_state                    VARCHAR(20) NOT NULL CHECK (condition_state IN ('NORMAL','DEGRADING','FAULT')),
    selected_warning_state             BOOLEAN NOT NULL,
    selected_warning_horizon_hours     INTEGER NOT NULL CHECK (selected_warning_horizon_hours IN (2,4,6)),
    source_data_origin                 VARCHAR(40) NOT NULL,
    scenario_type                      VARCHAR(60) NOT NULL,
    transformation_basis               VARCHAR(40) NOT NULL,
    degradation_signal_origin          VARCHAR(40) NOT NULL,
    PRIMARY KEY (equipment_id, event_timestamp)
);

CREATE TABLE IF NOT EXISTS analytics.metropt_pdm_warning_event (
    failure_id                         VARCHAR(64) NOT NULL,
    scenario_scope                     VARCHAR(80) NOT NULL,
    site_id                            INTEGER NOT NULL REFERENCES public.dim_site(site_id),
    equipment_id                       INTEGER NOT NULL REFERENCES public.dim_equipment(equipment_id),
    source_dataset_id                  INTEGER NOT NULL REFERENCES public.dim_source_dataset(source_dataset_id),
    scenario_source_dataset_id         INTEGER NOT NULL REFERENCES public.dim_source_dataset(source_dataset_id),
    warning_timestamp                  TIMESTAMP,
    fault_onset_timestamp              TIMESTAMP NOT NULL,
    fault_end_timestamp                TIMESTAMP NOT NULL,
    warning_horizon_hours              INTEGER NOT NULL CHECK (warning_horizon_hours IN (2,4,6)),
    warning_lead_time_hours            DOUBLE PRECISION CHECK (warning_lead_time_hours >= 0),
    warning_outcome                    VARCHAR(20) NOT NULL CHECK (warning_outcome IN ('WARNED','MISSED')),
    warning_persistence                VARCHAR(20) NOT NULL,
    source_data_origin                 VARCHAR(40) NOT NULL,
    scenario_type                      VARCHAR(60) NOT NULL,
    transformation_basis               VARCHAR(40) NOT NULL,
    degradation_signal_origin          VARCHAR(40) NOT NULL,
    PRIMARY KEY (scenario_scope, failure_id)
);

CREATE TABLE IF NOT EXISTS analytics.metropt_pdm_policy_kpi (
    scenario_scope                     VARCHAR(80) NOT NULL,
    model_name                         VARCHAR(100) NOT NULL,
    policy_name                        VARCHAR(120) NOT NULL,
    evaluation_split                   VARCHAR(40) NOT NULL,
    warning_horizon_hours              INTEGER NOT NULL CHECK (warning_horizon_hours IN (2,4,6)),
    events_evaluated                   INTEGER NOT NULL CHECK (events_evaluated >= 0),
    events_warned                      INTEGER NOT NULL CHECK (events_warned >= 0),
    events_missed                      INTEGER NOT NULL CHECK (events_missed >= 0),
    warning_success_rate               DOUBLE PRECISION NOT NULL CHECK (warning_success_rate BETWEEN 0 AND 1),
    average_lead_time_hours            DOUBLE PRECISION,
    median_lead_time_hours             DOUBLE PRECISION,
    precision_value                    DOUBLE PRECISION NOT NULL CHECK (precision_value BETWEEN 0 AND 1),
    recall_value                       DOUBLE PRECISION NOT NULL CHECK (recall_value BETWEEN 0 AND 1),
    false_alerts                       INTEGER NOT NULL CHECK (false_alerts >= 0),
    false_alerts_per_operating_day     DOUBLE PRECISION NOT NULL CHECK (false_alerts_per_operating_day >= 0),
    alert_episodes                     INTEGER NOT NULL CHECK (alert_episodes >= 0),
    operating_days                     DOUBLE PRECISION NOT NULL CHECK (operating_days > 0),
    is_selected                        BOOLEAN NOT NULL,
    PRIMARY KEY (scenario_scope, model_name, policy_name, evaluation_split, warning_horizon_hours)
);

CREATE INDEX IF NOT EXISTS idx_metropt_enterprise_telemetry_time
    ON analytics.metropt_enterprise_telemetry (event_timestamp);
CREATE INDEX IF NOT EXISTS idx_metropt_enterprise_telemetry_condition
    ON analytics.metropt_enterprise_telemetry (condition_state, selected_warning_state);
CREATE INDEX IF NOT EXISTS idx_metropt_pdm_warning_event_fault
    ON analytics.metropt_pdm_warning_event (fault_onset_timestamp);
