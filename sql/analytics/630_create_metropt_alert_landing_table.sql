-- Stage 12C optional database landing table.
-- The Python pipeline deliberately keeps real MetroPT analytics separate from
-- the synthetic enterprise integration facts.
--
-- This DDL is provided for a later Power BI/database integration step if needed.
-- Do not populate it until the Stage 12C model validation has been accepted.

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.metropt_anomaly_alert_episode (
    alert_id bigint PRIMARY KEY,
    alert_start timestamp without time zone NOT NULL,
    anomaly_score double precision,
    related_failure_id text,
    is_failure_related boolean,
    source_code text NOT NULL DEFAULT 'METROPT3_REAL',
    is_real_data boolean NOT NULL DEFAULT true
);
