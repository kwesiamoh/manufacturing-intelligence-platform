-- Stage 12A: Advanced Analytics source inventory
-- Read-only inventory. No objects are created or changed.

\pset pager off

\echo '=== Stage 12A candidate analytics objects ==='

WITH candidates(schema_name, object_name, analytics_role) AS (
    VALUES
        ('gold_bi','vw_shift_manufacturing_performance','production/quality/energy shift analytics'),
        ('gold_bi','vw_line_daily_performance','line-level production and energy trend analytics'),
        ('gold_bi','vw_site_daily_performance','site-level production and energy trend analytics'),
        ('gold','vw_data_quality_rule_status','existing DQ/anomaly rule status'),
        ('public','fact_quality','quality event source'),
        ('public','fact_production','production fact source'),
        ('public','fact_energy','energy fact source'),
        ('public','fact_telemetry','telemetry fact source'),
        ('public','vw_shift_production_kpi','production KPI source'),
        ('public','vw_line_daily_kpi','line daily KPI source'),
        ('public','vw_shift_energy_kpi','shift energy KPI source'),
        ('public','vw_line_daily_energy_kpi','line daily energy KPI source')
)
SELECT
    c.schema_name,
    c.object_name,
    c.analytics_role,
    CASE
        WHEN to_regclass(format('%I.%I', c.schema_name, c.object_name)) IS NOT NULL
        THEN 'EXISTS'
        ELSE 'MISSING'
    END AS object_status
FROM candidates c
ORDER BY c.analytics_role, c.schema_name, c.object_name;

\echo ''
\echo '=== Columns for existing candidate objects ==='

WITH candidates(schema_name, object_name) AS (
    VALUES
        ('gold_bi','vw_shift_manufacturing_performance'),
        ('gold_bi','vw_line_daily_performance'),
        ('gold_bi','vw_site_daily_performance'),
        ('gold','vw_data_quality_rule_status'),
        ('public','fact_quality'),
        ('public','fact_production'),
        ('public','fact_energy'),
        ('public','fact_telemetry'),
        ('public','vw_shift_production_kpi'),
        ('public','vw_line_daily_kpi'),
        ('public','vw_shift_energy_kpi'),
        ('public','vw_line_daily_energy_kpi')
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
\echo '=== Existing advanced-analytics-like objects already present ==='

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
       lower(c.relname) LIKE '%spc%'
    OR lower(c.relname) LIKE '%anomal%'
    OR lower(c.relname) LIKE '%forecast%'
    OR lower(c.relname) LIKE '%control%'
    OR lower(c.relname) LIKE '%telemetry%'
  )
ORDER BY n.nspname, c.relname;

\echo ''
\echo '=== Date coverage for Gold BI analytics grains ==='

SELECT
    'gold_bi.vw_shift_manufacturing_performance' AS object_name,
    MIN(date_id) AS min_date_id,
    MAX(date_id) AS max_date_id,
    COUNT(*) AS row_count
FROM gold_bi.vw_shift_manufacturing_performance
UNION ALL
SELECT
    'gold_bi.vw_line_daily_performance',
    MIN(date_id),
    MAX(date_id),
    COUNT(*)
FROM gold_bi.vw_line_daily_performance
UNION ALL
SELECT
    'gold_bi.vw_site_daily_performance',
    MIN(date_id),
    MAX(date_id),
    COUNT(*)
FROM gold_bi.vw_site_daily_performance;

\echo ''
\echo '=== Stage 12A inventory complete ==='
