-- Stage 4D/4E validation
WITH src AS (
    SELECT source_dataset_id
    FROM dim_source_dataset
    WHERE source_code = 'SYNTHETIC_ENTERPRISE'
)
SELECT 'fact_production' AS table_name, COUNT(*) AS row_count
FROM fact_production WHERE source_dataset_id=(SELECT source_dataset_id FROM src)
UNION ALL
SELECT 'fact_downtime', COUNT(*)
FROM fact_downtime WHERE source_dataset_id=(SELECT source_dataset_id FROM src)
UNION ALL
SELECT 'fact_quality', COUNT(*)
FROM fact_quality WHERE source_dataset_id=(SELECT source_dataset_id FROM src)
UNION ALL
SELECT 'fact_maintenance', COUNT(*)
FROM fact_maintenance WHERE source_dataset_id=(SELECT source_dataset_id FROM src)
UNION ALL
SELECT 'fact_energy', COUNT(*)
FROM fact_energy WHERE source_dataset_id=(SELECT source_dataset_id FROM src)
ORDER BY table_name;

\echo '=== Mandatory synthetic-fact-count gate ==='
DO $validation$
DECLARE
    synthetic_source_id bigint;
    expected record;
    actual_count bigint;
BEGIN
    SELECT source_dataset_id INTO STRICT synthetic_source_id
    FROM dim_source_dataset
    WHERE source_code = 'SYNTHETIC_ENTERPRISE';

    FOR expected IN
        SELECT * FROM (VALUES
            ('fact_production', 65790::bigint),
            ('fact_downtime', 170408::bigint),
            ('fact_quality', 257794::bigint),
            ('fact_maintenance', 46670::bigint),
            ('fact_energy', 65790::bigint)
        ) AS x(table_name, expected_count)
    LOOP
        EXECUTE format(
            'SELECT COUNT(*) FROM %I WHERE source_dataset_id = $1',
            expected.table_name
        ) INTO actual_count USING synthetic_source_id;
        IF actual_count <> expected.expected_count THEN
            RAISE EXCEPTION 'Synthetic fact % has % rows; expected %',
                expected.table_name, actual_count, expected.expected_count;
        END IF;
    END LOOP;
END
$validation$;
