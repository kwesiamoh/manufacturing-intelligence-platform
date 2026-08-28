-- Stage 13A.2: Reliability KPI feasibility and provenance
-- Read-only. No objects are created or modified.

\pset pager off

\echo '=== 1. Source distribution in maintenance facts ==='
SELECT
    m.source_dataset_id,
    s.source_code,
    s.source_name,
    s.integration_role,
    s.is_real_data,
    COUNT(*) AS maintenance_rows
FROM public.fact_maintenance m
LEFT JOIN public.dim_source_dataset s
  ON s.source_dataset_id = m.source_dataset_id
GROUP BY
    m.source_dataset_id, s.source_code, s.source_name,
    s.integration_role, s.is_real_data
ORDER BY maintenance_rows DESC;

\echo ''
\echo '=== 2. Source distribution in downtime facts ==='
SELECT
    d.source_dataset_id,
    s.source_code,
    s.source_name,
    s.integration_role,
    s.is_real_data,
    COUNT(*) AS downtime_rows
FROM public.fact_downtime d
LEFT JOIN public.dim_source_dataset s
  ON s.source_dataset_id = d.source_dataset_id
GROUP BY
    d.source_dataset_id, s.source_code, s.source_name,
    s.integration_role, s.is_real_data
ORDER BY downtime_rows DESC;

\echo ''
\echo '=== 3. Equipment source distribution ==='
SELECT
    e.source_dataset_id,
    s.source_code,
    s.source_name,
    s.integration_role,
    s.is_real_data,
    COUNT(*) AS equipment_rows
FROM public.dim_equipment e
LEFT JOIN public.dim_source_dataset s
  ON s.source_dataset_id = e.source_dataset_id
GROUP BY
    e.source_dataset_id, s.source_code, s.source_name,
    s.integration_role, s.is_real_data
ORDER BY equipment_rows DESC;

\echo ''
\echo '=== 4. Maintenance temporal and completeness profile ==='
SELECT
    COUNT(*) AS rows,
    MIN(start_timestamp) AS min_start,
    MAX(start_timestamp) AS max_start,
    COUNT(*) FILTER (WHERE end_timestamp IS NULL) AS null_end,
    COUNT(*) FILTER (WHERE duration_hours IS NULL) AS null_duration,
    COUNT(*) FILTER (WHERE equipment_id IS NULL) AS null_equipment,
    COUNT(*) FILTER (WHERE failure_reason_id IS NULL) AS null_failure_reason,
    COUNT(*) FILTER (WHERE planned_flag IS TRUE) AS planned_rows,
    COUNT(*) FILTER (WHERE planned_flag IS FALSE) AS unplanned_rows,
    COUNT(DISTINCT equipment_id) AS distinct_equipment,
    COUNT(DISTINCT work_order_id) AS distinct_work_orders
FROM public.fact_maintenance;

\echo ''
\echo '=== 5. Downtime temporal and completeness profile ==='
SELECT
    COUNT(*) AS rows,
    MIN(event_start) AS min_start,
    MAX(event_start) AS max_start,
    COUNT(*) FILTER (WHERE event_end IS NULL) AS null_end,
    COUNT(*) FILTER (WHERE duration_min IS NULL) AS null_duration,
    COUNT(*) FILTER (WHERE equipment_id IS NULL) AS null_equipment,
    COUNT(*) FILTER (WHERE failure_reason_id IS NULL) AS null_failure_reason,
    COUNT(*) FILTER (WHERE planned_flag IS TRUE) AS planned_rows,
    COUNT(*) FILTER (WHERE planned_flag IS FALSE) AS unplanned_rows,
    COUNT(DISTINCT equipment_id) AS distinct_equipment
FROM public.fact_downtime;

\echo ''
\echo '=== 6. Maintenance duration sanity ==='
SELECT
    COUNT(*) FILTER (WHERE duration_hours < 0) AS negative_duration,
    COUNT(*) FILTER (WHERE duration_hours = 0) AS zero_duration,
    COUNT(*) FILTER (
        WHERE start_timestamp IS NOT NULL
          AND end_timestamp IS NOT NULL
          AND end_timestamp < start_timestamp
    ) AS end_before_start,
    ROUND(MIN(duration_hours)::numeric, 4) AS min_duration_h,
    ROUND(AVG(duration_hours)::numeric, 4) AS avg_duration_h,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_hours)::numeric, 4) AS median_duration_h,
    ROUND(MAX(duration_hours)::numeric, 4) AS max_duration_h
FROM public.fact_maintenance
WHERE duration_hours IS NOT NULL;

\echo ''
\echo '=== 7. Downtime duration sanity ==='
SELECT
    COUNT(*) FILTER (WHERE duration_min < 0) AS negative_duration,
    COUNT(*) FILTER (WHERE duration_min = 0) AS zero_duration,
    COUNT(*) FILTER (
        WHERE event_start IS NOT NULL
          AND event_end IS NOT NULL
          AND event_end < event_start
    ) AS end_before_start,
    ROUND(MIN(duration_min)::numeric, 4) AS min_duration_min,
    ROUND(AVG(duration_min)::numeric, 4) AS avg_duration_min,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_min)::numeric, 4) AS median_duration_min,
    ROUND(MAX(duration_min)::numeric, 4) AS max_duration_min
FROM public.fact_downtime
WHERE duration_min IS NOT NULL;

\echo ''
\echo '=== 8. Maintenance types ==='
SELECT
    COALESCE(maintenance_type,'<NULL>') AS maintenance_type,
    planned_flag,
    COUNT(*) AS rows,
    ROUND(AVG(duration_hours)::numeric, 3) AS avg_duration_h
FROM public.fact_maintenance
GROUP BY maintenance_type, planned_flag
ORDER BY rows DESC, maintenance_type;

\echo ''
\echo '=== 9. Failure reason dimension schema and cardinality ==='
SELECT
    ordinal_position,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema='public'
  AND table_name='dim_failure_reason'
ORDER BY ordinal_position;

SELECT COUNT(*) AS failure_reason_rows
FROM public.dim_failure_reason;

\echo ''
\echo '=== 10. Equipment coverage by type / criticality ==='
SELECT
    COALESCE(equipment_type,'<NULL>') AS equipment_type,
    COALESCE(criticality_class,'<NULL>') AS criticality_class,
    COUNT(*) AS equipment_count,
    COUNT(*) FILTER (WHERE active_flag) AS active_equipment
FROM public.dim_equipment
GROUP BY equipment_type, criticality_class
ORDER BY equipment_count DESC, equipment_type, criticality_class;

\echo ''
\echo '=== 11. Equipment with event coverage ==='
SELECT
    COUNT(*) AS total_equipment,
    COUNT(*) FILTER (WHERE downtime_events > 0) AS equipment_with_downtime,
    COUNT(*) FILTER (WHERE maintenance_events > 0) AS equipment_with_maintenance,
    COUNT(*) FILTER (WHERE downtime_events > 0 AND maintenance_events > 0)
        AS equipment_with_both
FROM (
    SELECT
        e.equipment_id,
        COUNT(DISTINCT d.downtime_id) AS downtime_events,
        COUNT(DISTINCT m.maintenance_id) AS maintenance_events
    FROM public.dim_equipment e
    LEFT JOIN public.fact_downtime d
      ON d.equipment_id = e.equipment_id
    LEFT JOIN public.fact_maintenance m
      ON m.equipment_id = e.equipment_id
    GROUP BY e.equipment_id
) x;

\echo ''
\echo '=== 12. Direct maintenance-to-downtime link coverage ==='
SELECT
    COUNT(*) AS maintenance_rows,
    COUNT(*) FILTER (
        WHERE downtime_event_id IS NOT NULL
          AND btrim(downtime_event_id) <> ''
    ) AS maintenance_rows_with_downtime_reference,
    COUNT(DISTINCT downtime_event_id) FILTER (
        WHERE downtime_event_id IS NOT NULL
          AND btrim(downtime_event_id) <> ''
    ) AS distinct_downtime_references
FROM public.fact_maintenance;

\echo ''
\echo '=== Stage 13A.2 complete ==='
