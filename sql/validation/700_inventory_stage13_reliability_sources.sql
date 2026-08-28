-- Stage 13A: Maintenance & Reliability source inventory
-- Read-only. No objects are created or modified.

\pset pager off

\echo '=== 1. Candidate maintenance/reliability database objects ==='

SELECT
    n.nspname AS schema_name,
    c.relname AS object_name,
    CASE c.relkind
        WHEN 'r' THEN 'table'
        WHEN 'v' THEN 'view'
        WHEN 'm' THEN 'materialized view'
        ELSE c.relkind::text
    END AS object_type
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname NOT IN ('pg_catalog','information_schema')
  AND (
       lower(c.relname) LIKE '%maintenance%'
    OR lower(c.relname) LIKE '%failure%'
    OR lower(c.relname) LIKE '%reliab%'
    OR lower(c.relname) LIKE '%downtime%'
    OR lower(c.relname) LIKE '%equipment%'
    OR lower(c.relname) LIKE '%asset%'
  )
ORDER BY n.nspname, c.relname;

\echo ''
\echo '=== 2. Candidate fact/dimension columns ==='

WITH candidates(schema_name, object_name) AS (
    VALUES
        ('public','fact_maintenance'),
        ('public','fact_downtime'),
        ('public','dim_equipment'),
        ('public','dim_failure_mode'),
        ('public','vw_downtime_reason_pareto')
)
SELECT
    c.table_schema,
    c.table_name,
    c.ordinal_position,
    c.column_name,
    c.data_type
FROM information_schema.columns c
JOIN candidates x
  ON x.schema_name = c.table_schema
 AND x.object_name = c.table_name
ORDER BY c.table_schema, c.table_name, c.ordinal_position;

\echo ''
\echo '=== 3. Candidate object row counts ==='

DO $$
DECLARE
    r record;
    n bigint;
BEGIN
    FOR r IN
        SELECT * FROM (VALUES
            ('public','fact_maintenance'),
            ('public','fact_downtime'),
            ('public','dim_equipment'),
            ('public','dim_failure_mode'),
            ('public','vw_downtime_reason_pareto')
        ) v(schema_name, object_name)
    LOOP
        IF to_regclass(format('%I.%I', r.schema_name, r.object_name)) IS NOT NULL THEN
            EXECUTE format('SELECT count(*) FROM %I.%I', r.schema_name, r.object_name)
            INTO n;
            RAISE NOTICE '%.% = % rows', r.schema_name, r.object_name, n;
        ELSE
            RAISE NOTICE '%.% = MISSING', r.schema_name, r.object_name;
        END IF;
    END LOOP;
END $$;

\echo ''
\echo '=== 4. Source dataset records related to maintenance/reliability ==='

SELECT
    source_dataset_id,
    source_code,
    source_name,
    publisher,
    source_domain,
    integration_role,
    is_real_data,
    reference_period,
    notes
FROM public.dim_source_dataset
WHERE lower(coalesce(source_domain,'')) LIKE '%maint%'
   OR lower(coalesce(source_domain,'')) LIKE '%reliab%'
   OR lower(coalesce(source_name,'')) LIKE '%maint%'
   OR lower(coalesce(source_name,'')) LIKE '%reliab%'
   OR lower(coalesce(source_code,'')) LIKE '%maint%'
   OR lower(coalesce(source_code,'')) LIKE '%reliab%'
ORDER BY source_dataset_id;

\echo ''
\echo '=== Stage 13A database inventory complete ==='
