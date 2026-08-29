\set ON_ERROR_STOP on

DO $$
DECLARE
    telemetry_rows BIGINT;
    warning_rows BIGINT;
    selected_rows BIGINT;
BEGIN
    SELECT COUNT(*) INTO telemetry_rows
    FROM analytics.metropt_enterprise_telemetry;
    IF telemetry_rows = 0 THEN
        RAISE EXCEPTION 'MetroPT enterprise telemetry is empty';
    END IF;

    SELECT COUNT(*) INTO warning_rows
    FROM analytics.metropt_pdm_warning_event;
    IF warning_rows = 0 THEN
        RAISE EXCEPTION 'MetroPT predictive-maintenance warning events are empty';
    END IF;

    SELECT COUNT(*) INTO selected_rows
    FROM analytics.metropt_pdm_policy_kpi
    WHERE is_selected;
    IF selected_rows <> 2 THEN
        RAISE EXCEPTION 'Expected two selected MetroPT policies, found %', selected_rows;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM analytics.metropt_enterprise_telemetry t
        LEFT JOIN public.dim_site s ON s.site_id = t.site_id
        LEFT JOIN public.dim_equipment e ON e.equipment_id = t.equipment_id
        WHERE s.site_id IS NULL
           OR e.equipment_id IS NULL
           OR e.equipment_type <> 'COMPRESSED_AIR_SYSTEM'
    ) THEN
        RAISE EXCEPTION 'Orphan or non-compressor enterprise telemetry mapping found';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM analytics.metropt_enterprise_telemetry
        WHERE source_data_origin <> 'EXTERNAL_REAL'
           OR scenario_type <> 'SYNTHETIC_ENTERPRISE_ADAPTATION'
           OR transformation_basis <> 'METROPT_INFORMED'
           OR degradation_signal_origin <> 'SYNTHETIC_CONTROLLED'
    ) THEN
        RAISE EXCEPTION 'MetroPT enterprise telemetry lineage is invalid';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM analytics.metropt_pdm_warning_event
        WHERE warning_outcome = 'WARNED'
          AND (warning_timestamp >= fault_onset_timestamp OR warning_lead_time_hours < 0)
    ) THEN
        RAISE EXCEPTION 'Invalid predictive warning timing found';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM gold.vw_compressor_predictive_maintenance_detail
    ) OR NOT EXISTS (
        SELECT 1 FROM gold.vw_compressor_predictive_maintenance_kpi
    ) THEN
        RAISE EXCEPTION 'MetroPT Gold reporting views are empty';
    END IF;
END $$;

SELECT
    'metropt_enterprise_telemetry' AS object_name,
    COUNT(*) AS row_count,
    MIN(event_timestamp) AS minimum_timestamp,
    MAX(event_timestamp) AS maximum_timestamp
FROM analytics.metropt_enterprise_telemetry;

SELECT
    scenario_scope,
    model_name,
    selected_warning_policy,
    selected_warning_horizon_hours,
    events_evaluated,
    events_warned,
    events_missed,
    median_lead_time_hours,
    precision,
    recall,
    false_alerts_per_operating_day
FROM gold.vw_compressor_predictive_maintenance_kpi
ORDER BY scenario_scope;

DO $$
DECLARE
    v_rows bigint;
    v_events bigint;
    v_warning_points bigint;
    v_fault_onsets bigint;
BEGIN
    SELECT
        COUNT(*),
        COUNT(DISTINCT failure_id),
        COUNT(*) FILTER (WHERE is_warning_point),
        COUNT(*) FILTER (WHERE is_fault_onset)
    INTO
        v_rows,
        v_events,
        v_warning_points,
        v_fault_onsets
    FROM gold.vw_compressor_predictive_maintenance_timeline;

    IF v_rows = 0 THEN
        RAISE EXCEPTION 'Predictive-maintenance timeline view is empty';
    END IF;

    IF v_events <> 4 THEN
        RAISE EXCEPTION 'Expected 4 controlled PdM events, found %', v_events;
    END IF;

    IF v_warning_points <> v_events THEN
        RAISE EXCEPTION 'Expected one warning point per event';
    END IF;

    IF v_fault_onsets <> v_events THEN
        RAISE EXCEPTION 'Expected one fault onset per event';
    END IF;
END
$$;