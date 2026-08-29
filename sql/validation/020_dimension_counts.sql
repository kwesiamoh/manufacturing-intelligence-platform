SELECT 'dim_source_dataset' AS table_name, COUNT(*) AS row_count FROM dim_source_dataset
UNION ALL SELECT 'dim_site', COUNT(*) FROM dim_site
UNION ALL SELECT 'dim_area', COUNT(*) FROM dim_area
UNION ALL SELECT 'dim_line', COUNT(*) FROM dim_line
UNION ALL SELECT 'dim_equipment', COUNT(*) FROM dim_equipment
UNION ALL SELECT 'dim_sensor', COUNT(*) FROM dim_sensor
UNION ALL SELECT 'dim_product', COUNT(*) FROM dim_product
UNION ALL SELECT 'dim_shift', COUNT(*) FROM dim_shift
UNION ALL SELECT 'dim_failure_reason', COUNT(*) FROM dim_failure_reason
UNION ALL SELECT 'dim_utility', COUNT(*) FROM dim_utility
UNION ALL SELECT 'dim_time', COUNT(*) FROM dim_time
ORDER BY table_name;

\echo '=== Mandatory dimension-count gate ==='
DO $validation$
DECLARE
    expected record;
    actual_count bigint;
BEGIN
    FOR expected IN
        SELECT * FROM (VALUES
            ('dim_source_dataset', 16::bigint),
            ('dim_site', 6::bigint),
            ('dim_area', 12::bigint),
            ('dim_line', 30::bigint),
            ('dim_equipment', 255::bigint),
            ('dim_sensor', 0::bigint),
            ('dim_product', 6::bigint),
            ('dim_shift', 3::bigint),
            ('dim_failure_reason', 23::bigint),
            ('dim_utility', 7::bigint),
            ('dim_time', 8035::bigint)
        ) AS x(table_name, expected_count)
    LOOP
        EXECUTE format('SELECT COUNT(*) FROM %I', expected.table_name)
        INTO actual_count;
        IF actual_count <> expected.expected_count THEN
            RAISE EXCEPTION 'Dimension % has % rows; expected %',
                expected.table_name, actual_count, expected.expected_count;
        END IF;
    END LOOP;
END
$validation$;
