-- Stage 12A.2: Advanced analytics feasibility profile
-- Read-only. No database objects are created or modified.

\pset pager off

\echo '=== 1. Core fact row counts ==='
SELECT 'fact_production' AS object_name, COUNT(*) AS row_count FROM public.fact_production
UNION ALL
SELECT 'fact_quality', COUNT(*) FROM public.fact_quality
UNION ALL
SELECT 'fact_energy', COUNT(*) FROM public.fact_energy
UNION ALL
SELECT 'fact_telemetry', COUNT(*) FROM public.fact_telemetry
ORDER BY object_name;

\echo ''
\echo '=== 2. Quality measurement/SPC feasibility ==='
SELECT
    COUNT(*) AS quality_rows,
    COUNT(measurement_value) AS measurement_value_rows,
    COUNT(*) FILTER (
        WHERE measurement_value IS NOT NULL
          AND lower_spec_limit IS NOT NULL
          AND upper_spec_limit IS NOT NULL
    ) AS rows_with_measurement_and_both_specs,
    COUNT(*) FILTER (WHERE lower_spec_limit IS NOT NULL) AS lower_spec_rows,
    COUNT(*) FILTER (WHERE upper_spec_limit IS NOT NULL) AS upper_spec_rows,
    COUNT(DISTINCT defect_code) AS distinct_defect_codes,
    COUNT(DISTINCT product_id) AS distinct_products,
    COUNT(DISTINCT line_id) AS distinct_lines,
    MIN(timestamp) AS min_timestamp,
    MAX(timestamp) AS max_timestamp
FROM public.fact_quality;

\echo ''
\echo '=== 3. Quality measurement distributions by defect/result ==='
SELECT
    COALESCE(quality_result, '<NULL>') AS quality_result,
    COALESCE(defect_code, '<NULL>') AS defect_code,
    COUNT(*) AS rows,
    COUNT(measurement_value) AS measurement_rows,
    COUNT(*) FILTER (
        WHERE measurement_value IS NOT NULL
          AND lower_spec_limit IS NOT NULL
          AND upper_spec_limit IS NOT NULL
    ) AS measurement_with_specs_rows
FROM public.fact_quality
GROUP BY quality_result, defect_code
ORDER BY rows DESC, quality_result, defect_code;

\echo ''
\echo '=== 4. Telemetry feasibility ==='
SELECT
    COUNT(*) AS telemetry_rows,
    COUNT(DISTINCT sensor_id) AS distinct_sensor_ids,
    COUNT(DISTINCT equipment_id) AS distinct_equipment_ids,
    COUNT(DISTINCT source_dataset_id) AS distinct_source_datasets,
    COUNT(measurement_value) AS measurement_rows,
    COUNT(*) FILTER (WHERE measurement_value IS NULL) AS null_measurement_rows,
    COUNT(*) FILTER (WHERE quality_flag IS NOT NULL) AS quality_flag_rows,
    MIN(timestamp) AS min_timestamp,
    MAX(timestamp) AS max_timestamp
FROM public.fact_telemetry;

\echo ''
\echo '=== 5. Telemetry rows by source dataset / unit / quality flag ==='
SELECT
    source_dataset_id,
    COALESCE(engineering_unit, '<NULL>') AS engineering_unit,
    COALESCE(quality_flag, '<NULL>') AS quality_flag,
    COUNT(*) AS rows,
    COUNT(DISTINCT sensor_id) AS distinct_sensor_ids,
    COUNT(DISTINCT equipment_id) AS distinct_equipment_ids
FROM public.fact_telemetry
GROUP BY source_dataset_id, engineering_unit, quality_flag
ORDER BY rows DESC, source_dataset_id;

\echo ''
\echo '=== 6. Production-series feasibility ==='
SELECT
    COUNT(*) AS production_rows,
    COUNT(DISTINCT line_id) AS distinct_lines,
    COUNT(DISTINCT product_id) AS distinct_products,
    COUNT(DISTINCT shift_id) AS distinct_shifts,
    MIN(timestamp_start) AS min_timestamp,
    MAX(timestamp_start) AS max_timestamp,
    COUNT(*) FILTER (WHERE actual_quantity IS NULL) AS null_actual_quantity,
    COUNT(*) FILTER (WHERE planned_quantity IS NULL) AS null_planned_quantity,
    COUNT(*) FILTER (WHERE planned_production_time_min IS NULL) AS null_planned_time
FROM public.fact_production;

\echo ''
\echo '=== 7. Energy-series feasibility ==='
SELECT
    COUNT(*) AS energy_rows,
    COUNT(DISTINCT site_id) AS distinct_sites,
    COUNT(DISTINCT line_id) AS distinct_lines,
    COUNT(DISTINCT utility_id) AS distinct_utilities,
    COUNT(DISTINCT source_dataset_id) AS distinct_source_datasets,
    MIN(timestamp) AS min_timestamp,
    MAX(timestamp) AS max_timestamp,
    COUNT(*) FILTER (WHERE consumption IS NULL) AS null_consumption,
    COUNT(*) FILTER (WHERE demand IS NULL) AS null_demand
FROM public.fact_energy;

\echo ''
\echo '=== 8. Source dataset IDs used by analytics candidate facts ==='
SELECT 'production' AS fact_domain, source_dataset_id, COUNT(*) AS rows
FROM public.fact_production
GROUP BY source_dataset_id
UNION ALL
SELECT 'quality', source_dataset_id, COUNT(*)
FROM public.fact_quality
GROUP BY source_dataset_id
UNION ALL
SELECT 'energy', source_dataset_id, COUNT(*)
FROM public.fact_energy
GROUP BY source_dataset_id
UNION ALL
SELECT 'telemetry', source_dataset_id, COUNT(*)
FROM public.fact_telemetry
GROUP BY source_dataset_id
ORDER BY fact_domain, source_dataset_id;

\echo ''
\echo '=== 9. dim_source_dataset schema for provenance follow-up ==='
SELECT
    ordinal_position,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'dim_source_dataset'
ORDER BY ordinal_position;

\echo ''
\echo '=== Stage 12A.2 feasibility profile complete ==='
