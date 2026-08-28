-- database integrity database validation
-- Run against manufacturing_intelligence.

\pset pager off

\echo '=== Dimension row counts ==='
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

\echo '=== Synthetic fact row counts ==='
WITH src AS (
    SELECT source_dataset_id
    FROM dim_source_dataset
    WHERE source_code='SYNTHETIC_ENTERPRISE'
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

\echo '=== Reference row counts ==='
SELECT 'ref_itac_assessment' AS table_name, COUNT(*) AS row_count FROM ref_itac_assessment
UNION ALL SELECT 'ref_itac_recommendation', COUNT(*) FROM ref_itac_recommendation
UNION ALL SELECT 'ref_fmucd_maintenance', COUNT(*) FROM ref_fmucd_maintenance
UNION ALL SELECT 'ref_statcan_water', COUNT(*) FROM ref_statcan_water
UNION ALL SELECT 'ref_eia_mecs', COUNT(*) FROM ref_eia_mecs
UNION ALL SELECT 'ref_eu_ets', COUNT(*) FROM ref_eu_ets
UNION ALL SELECT 'ref_eurostat_energy_price', COUNT(*) FROM ref_eurostat_energy_price
ORDER BY table_name;

\echo '=== Orphan checks: expected all zero ==='
WITH src AS (
    SELECT source_dataset_id FROM dim_source_dataset
    WHERE source_code='SYNTHETIC_ENTERPRISE'
)
SELECT 'downtime_to_production' AS check_name, COUNT(*) AS orphan_count
FROM fact_downtime d
LEFT JOIN fact_production p
  ON p.source_dataset_id=d.source_dataset_id
 AND p.source_record_id=d.production_record_id
WHERE d.source_dataset_id=(SELECT source_dataset_id FROM src)
  AND p.production_id IS NULL
UNION ALL
SELECT 'quality_to_production', COUNT(*)
FROM fact_quality q
LEFT JOIN fact_production p
  ON p.source_dataset_id=q.source_dataset_id
 AND p.source_record_id=q.production_record_id
WHERE q.source_dataset_id=(SELECT source_dataset_id FROM src)
  AND p.production_id IS NULL
UNION ALL
SELECT 'maintenance_to_downtime', COUNT(*)
FROM fact_maintenance m
LEFT JOIN fact_downtime d
  ON d.source_dataset_id=m.downtime_source_dataset_id
 AND d.source_record_id=m.downtime_event_id
WHERE m.source_dataset_id=(SELECT source_dataset_id FROM src)
  AND d.downtime_id IS NULL
UNION ALL
SELECT 'energy_to_production', COUNT(*)
FROM fact_energy e
LEFT JOIN fact_production p
  ON p.source_dataset_id=e.source_dataset_id
 AND p.source_record_id=e.production_record_id
WHERE e.source_dataset_id=(SELECT source_dataset_id FROM src)
  AND p.production_id IS NULL;

\echo '=== Duplicate source record checks: expected all zero ==='
WITH src AS (
    SELECT source_dataset_id FROM dim_source_dataset
    WHERE source_code='SYNTHETIC_ENTERPRISE'
)
SELECT 'production_source_record' AS check_name, COUNT(*) AS duplicate_groups
FROM (
    SELECT source_record_id
    FROM fact_production
    WHERE source_dataset_id=(SELECT source_dataset_id FROM src)
    GROUP BY source_record_id HAVING COUNT(*) > 1
) x
UNION ALL
SELECT 'downtime_source_record', COUNT(*)
FROM (
    SELECT source_record_id
    FROM fact_downtime
    WHERE source_dataset_id=(SELECT source_dataset_id FROM src)
    GROUP BY source_record_id HAVING COUNT(*) > 1
) x
UNION ALL
SELECT 'quality_source_record', COUNT(*)
FROM (
    SELECT source_record_id
    FROM fact_quality
    WHERE source_dataset_id=(SELECT source_dataset_id FROM src)
    GROUP BY source_record_id HAVING COUNT(*) > 1
) x
UNION ALL
SELECT 'maintenance_source_record', COUNT(*)
FROM (
    SELECT source_record_id
    FROM fact_maintenance
    WHERE source_dataset_id=(SELECT source_dataset_id FROM src)
    GROUP BY source_record_id HAVING COUNT(*) > 1
) x
UNION ALL
SELECT 'energy_source_record', COUNT(*)
FROM (
    SELECT source_record_id
    FROM fact_energy
    WHERE source_dataset_id=(SELECT source_dataset_id FROM src)
    GROUP BY source_record_id HAVING COUNT(*) > 1
) x;

\echo '=== Required-null checks: expected all zero ==='
WITH src AS (
    SELECT source_dataset_id FROM dim_source_dataset
    WHERE source_code='SYNTHETIC_ENTERPRISE'
)
SELECT 'production_required_nulls' AS check_name, COUNT(*) AS bad_rows
FROM fact_production
WHERE source_dataset_id=(SELECT source_dataset_id FROM src)
  AND (
    timestamp_start IS NULL OR timestamp_end IS NULL OR date_id IS NULL
    OR site_id IS NULL OR line_id IS NULL OR product_id IS NULL OR shift_id IS NULL
    OR planned_quantity IS NULL OR actual_quantity IS NULL
    OR good_quantity IS NULL OR reject_quantity IS NULL
    OR operating_time_min IS NULL OR planned_production_time_min IS NULL
    OR source_record_id IS NULL
  )
UNION ALL
SELECT 'downtime_required_nulls', COUNT(*)
FROM fact_downtime
WHERE source_dataset_id=(SELECT source_dataset_id FROM src)
  AND (
    event_start IS NULL OR event_end IS NULL OR site_id IS NULL OR line_id IS NULL
    OR duration_min IS NULL OR planned_flag IS NULL
    OR source_record_id IS NULL OR production_record_id IS NULL
  )
UNION ALL
SELECT 'quality_required_nulls', COUNT(*)
FROM fact_quality
WHERE source_dataset_id=(SELECT source_dataset_id FROM src)
  AND (
    timestamp IS NULL OR site_id IS NULL OR line_id IS NULL OR product_id IS NULL
    OR reject_quantity IS NULL OR source_record_id IS NULL OR production_record_id IS NULL
  )
UNION ALL
SELECT 'maintenance_required_nulls', COUNT(*)
FROM fact_maintenance
WHERE source_dataset_id=(SELECT source_dataset_id FROM src)
  AND (
    site_id IS NULL OR equipment_id IS NULL OR work_order_id IS NULL
    OR start_timestamp IS NULL OR end_timestamp IS NULL
    OR duration_hours IS NULL OR labor_hours IS NULL
    OR source_record_id IS NULL OR downtime_source_dataset_id IS NULL
    OR downtime_event_id IS NULL
  )
UNION ALL
SELECT 'energy_required_nulls', COUNT(*)
FROM fact_energy
WHERE source_dataset_id=(SELECT source_dataset_id FROM src)
  AND (
    timestamp IS NULL OR site_id IS NULL OR line_id IS NULL OR utility_id IS NULL
    OR consumption IS NULL OR measurement_unit IS NULL
    OR source_record_id IS NULL OR production_record_id IS NULL
  );

\echo '=== Production quantity reconciliation: expected zero bad rows ==='
WITH src AS (
    SELECT source_dataset_id FROM dim_source_dataset
    WHERE source_code='SYNTHETIC_ENTERPRISE'
)
SELECT COUNT(*) AS bad_rows
FROM fact_production
WHERE source_dataset_id=(SELECT source_dataset_id FROM src)
  AND actual_quantity <> good_quantity + reject_quantity;

\echo '=== Production time sanity: expected zero bad rows ==='
WITH src AS (
    SELECT source_dataset_id FROM dim_source_dataset
    WHERE source_code='SYNTHETIC_ENTERPRISE'
)
SELECT COUNT(*) AS bad_rows
FROM fact_production
WHERE source_dataset_id=(SELECT source_dataset_id FROM src)
  AND (
    operating_time_min < 0
    OR planned_production_time_min < 0
    OR operating_time_min > planned_production_time_min
    OR timestamp_end <= timestamp_start
  );

\echo '=== Downtime duration sanity: expected zero bad rows ==='
WITH src AS (
    SELECT source_dataset_id FROM dim_source_dataset
    WHERE source_code='SYNTHETIC_ENTERPRISE'
)
SELECT COUNT(*) AS bad_rows
FROM fact_downtime
WHERE source_dataset_id=(SELECT source_dataset_id FROM src)
  AND (
    duration_min <= 0
    OR event_end <= event_start
    OR ABS(duration_min - EXTRACT(EPOCH FROM (event_end-event_start))/60.0) > 0.001
  );

\echo '=== Maintenance interval sanity: expected zero bad rows ==='
WITH src AS (
    SELECT source_dataset_id FROM dim_source_dataset
    WHERE source_code='SYNTHETIC_ENTERPRISE'
)
SELECT COUNT(*) AS bad_rows
FROM fact_maintenance
WHERE source_dataset_id=(SELECT source_dataset_id FROM src)
  AND (
    duration_hours <= 0
    OR labor_hours < 0
    OR end_timestamp <= start_timestamp
    OR ABS(duration_hours - EXTRACT(EPOCH FROM (end_timestamp-start_timestamp))/3600.0) > 0.001
  );

\echo '=== Energy sanity: expected zero bad rows ==='
WITH src AS (
    SELECT source_dataset_id FROM dim_source_dataset
    WHERE source_code='SYNTHETIC_ENTERPRISE'
)
SELECT COUNT(*) AS bad_rows
FROM fact_energy
WHERE source_dataset_id=(SELECT source_dataset_id FROM src)
  AND (
    consumption <= 0
    OR demand <= 0
    OR measurement_unit <> 'kWh'
  );

\echo '=== database integrity SQL validation complete ==='

\echo '=== Mandatory database integrity integrity gate ==='
DO $validation$
DECLARE
    synthetic_source_id bigint;
    bad_count bigint;
BEGIN
    SELECT source_dataset_id INTO STRICT synthetic_source_id
    FROM dim_source_dataset
    WHERE source_code = 'SYNTHETIC_ENTERPRISE';

    SELECT SUM(n) INTO bad_count
    FROM (
        SELECT COUNT(*) AS n FROM fact_downtime d
        LEFT JOIN fact_production p
          ON p.source_dataset_id = d.source_dataset_id
         AND p.source_record_id = d.production_record_id
        WHERE d.source_dataset_id = synthetic_source_id AND p.production_id IS NULL
        UNION ALL
        SELECT COUNT(*) FROM fact_quality q
        LEFT JOIN fact_production p
          ON p.source_dataset_id = q.source_dataset_id
         AND p.source_record_id = q.production_record_id
        WHERE q.source_dataset_id = synthetic_source_id AND p.production_id IS NULL
        UNION ALL
        SELECT COUNT(*) FROM fact_maintenance m
        LEFT JOIN fact_downtime d
          ON d.source_dataset_id = m.downtime_source_dataset_id
         AND d.source_record_id = m.downtime_event_id
        WHERE m.source_dataset_id = synthetic_source_id AND d.downtime_id IS NULL
        UNION ALL
        SELECT COUNT(*) FROM fact_energy e
        LEFT JOIN fact_production p
          ON p.source_dataset_id = e.source_dataset_id
         AND p.source_record_id = e.production_record_id
        WHERE e.source_dataset_id = synthetic_source_id AND p.production_id IS NULL
    ) orphan_checks;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'database integrity lineage gate found % orphan rows', bad_count;
    END IF;

    SELECT SUM(n) INTO bad_count
    FROM (
        SELECT COUNT(*) AS n FROM (
            SELECT source_record_id FROM fact_production
            WHERE source_dataset_id = synthetic_source_id
            GROUP BY source_record_id HAVING COUNT(*) > 1
        ) x
        UNION ALL SELECT COUNT(*) FROM (
            SELECT source_record_id FROM fact_downtime
            WHERE source_dataset_id = synthetic_source_id
            GROUP BY source_record_id HAVING COUNT(*) > 1
        ) x
        UNION ALL SELECT COUNT(*) FROM (
            SELECT source_record_id FROM fact_quality
            WHERE source_dataset_id = synthetic_source_id
            GROUP BY source_record_id HAVING COUNT(*) > 1
        ) x
        UNION ALL SELECT COUNT(*) FROM (
            SELECT source_record_id FROM fact_maintenance
            WHERE source_dataset_id = synthetic_source_id
            GROUP BY source_record_id HAVING COUNT(*) > 1
        ) x
        UNION ALL SELECT COUNT(*) FROM (
            SELECT source_record_id FROM fact_energy
            WHERE source_dataset_id = synthetic_source_id
            GROUP BY source_record_id HAVING COUNT(*) > 1
        ) x
    ) duplicate_checks;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'database integrity uniqueness gate found % duplicate source-record groups', bad_count;
    END IF;

    SELECT SUM(n) INTO bad_count
    FROM (
        SELECT COUNT(*) AS n FROM fact_production
        WHERE source_dataset_id = synthetic_source_id AND (
            timestamp_start IS NULL OR timestamp_end IS NULL OR date_id IS NULL
            OR site_id IS NULL OR line_id IS NULL OR product_id IS NULL
            OR shift_id IS NULL OR planned_quantity IS NULL
            OR actual_quantity IS NULL OR good_quantity IS NULL
            OR reject_quantity IS NULL OR operating_time_min IS NULL
            OR planned_production_time_min IS NULL OR source_record_id IS NULL)
        UNION ALL SELECT COUNT(*) FROM fact_downtime
        WHERE source_dataset_id = synthetic_source_id AND (
            event_start IS NULL OR event_end IS NULL OR site_id IS NULL
            OR line_id IS NULL OR duration_min IS NULL OR planned_flag IS NULL
            OR source_record_id IS NULL OR production_record_id IS NULL)
        UNION ALL SELECT COUNT(*) FROM fact_quality
        WHERE source_dataset_id = synthetic_source_id AND (
            timestamp IS NULL OR site_id IS NULL OR line_id IS NULL
            OR product_id IS NULL OR reject_quantity IS NULL
            OR source_record_id IS NULL OR production_record_id IS NULL)
        UNION ALL SELECT COUNT(*) FROM fact_maintenance
        WHERE source_dataset_id = synthetic_source_id AND (
            site_id IS NULL OR equipment_id IS NULL OR work_order_id IS NULL
            OR start_timestamp IS NULL OR end_timestamp IS NULL
            OR duration_hours IS NULL OR labor_hours IS NULL
            OR source_record_id IS NULL OR downtime_source_dataset_id IS NULL
            OR downtime_event_id IS NULL)
        UNION ALL SELECT COUNT(*) FROM fact_energy
        WHERE source_dataset_id = synthetic_source_id AND (
            timestamp IS NULL OR site_id IS NULL OR line_id IS NULL
            OR utility_id IS NULL OR consumption IS NULL
            OR measurement_unit IS NULL OR source_record_id IS NULL
            OR production_record_id IS NULL)
    ) required_null_checks;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'database integrity completeness gate found % rows with required nulls', bad_count;
    END IF;

    SELECT SUM(n) INTO bad_count
    FROM (
        SELECT COUNT(*) AS n FROM fact_production
        WHERE source_dataset_id = synthetic_source_id
          AND (actual_quantity <> good_quantity + reject_quantity
               OR operating_time_min < 0 OR planned_production_time_min < 0
               OR operating_time_min > planned_production_time_min
               OR timestamp_end <= timestamp_start)
        UNION ALL SELECT COUNT(*) FROM fact_downtime
        WHERE source_dataset_id = synthetic_source_id
          AND (duration_min <= 0 OR event_end <= event_start
               OR ABS(duration_min - EXTRACT(EPOCH FROM (event_end-event_start))/60.0) > 0.001)
        UNION ALL SELECT COUNT(*) FROM fact_maintenance
        WHERE source_dataset_id = synthetic_source_id
          AND (duration_hours <= 0 OR labor_hours < 0 OR end_timestamp <= start_timestamp
               OR ABS(duration_hours - EXTRACT(EPOCH FROM (end_timestamp-start_timestamp))/3600.0) > 0.001)
        UNION ALL SELECT COUNT(*) FROM fact_energy
        WHERE source_dataset_id = synthetic_source_id
          AND (consumption <= 0 OR demand <= 0 OR measurement_unit <> 'kWh')
    ) business_rule_checks;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'database integrity business-rule gate found % invalid rows', bad_count;
    END IF;
END
$validation$;
