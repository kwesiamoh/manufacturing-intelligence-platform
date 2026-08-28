-- database verification

SELECT current_database() AS database_name;

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND (
      table_name LIKE 'dim_%'
      OR table_name LIKE 'fact_%'
  )
ORDER BY table_name;

SELECT
    COUNT(*) FILTER (WHERE table_name LIKE 'dim_%') AS dimension_table_count,
    COUNT(*) FILTER (WHERE table_name LIKE 'fact_%') AS fact_table_count
FROM information_schema.tables
WHERE table_schema = 'public';

\echo '=== Mandatory base-schema gate ==='
DO $validation$
DECLARE
    missing_objects text;
BEGIN
    SELECT string_agg(object_name, ', ' ORDER BY object_name)
    INTO missing_objects
    FROM unnest(ARRAY[
        'dim_source_dataset', 'dim_site', 'dim_area', 'dim_line',
        'dim_equipment', 'dim_sensor', 'dim_product', 'dim_shift',
        'dim_failure_reason', 'dim_utility', 'dim_time',
        'fact_telemetry', 'fact_production', 'fact_downtime',
        'fact_quality', 'fact_maintenance', 'fact_energy', 'fact_utility',
        'fact_water', 'fact_emissions', 'fact_energy_price',
        'fact_production_order', 'fact_weather_context', 'fact_data_quality'
    ]) AS required(object_name)
    WHERE to_regclass('public.' || object_name) IS NULL;

    IF missing_objects IS NOT NULL THEN
        RAISE EXCEPTION 'Mandatory base schema objects are missing: %', missing_objects;
    END IF;
END
$validation$;
