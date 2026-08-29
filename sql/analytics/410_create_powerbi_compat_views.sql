-- Power BI compatibility Power BI compatibility layer
-- Purpose:
--   PostgreSQL unconstrained NUMERIC values can exceed the precision metadata
--   supported by the .NET System.Decimal provider used by Power BI.
--
-- Design:
--   Keep the validated gold.* views unchanged.
--   Create thin gold_bi.* wrapper views for Power BI.
--   Only unconstrained NUMERIC columns (numeric_precision IS NULL) are cast
--   to DOUBLE PRECISION. Constrained NUMERIC columns and all non-NUMERIC
--   columns are preserved as-is.
--
-- This is a reporting compatibility layer, not a change to business logic.

BEGIN;

CREATE SCHEMA IF NOT EXISTS gold_bi;

DO $$
DECLARE
    src_view text;
    select_list text;
    ddl text;
BEGIN
    FOREACH src_view IN ARRAY ARRAY[
        'vw_shift_manufacturing_performance',
        'vw_line_daily_performance',
        'vw_site_daily_performance',
        'vw_site_executive_summary',
        'vw_data_quality_domain_summary',
        'vw_data_quality_rule_status'
    ]
    LOOP
        SELECT string_agg(
            CASE
                WHEN data_type = 'numeric' AND numeric_precision IS NULL
                    THEN format('%I::double precision AS %I', column_name, column_name)
                ELSE format('%I', column_name)
            END,
            E',\n    ' ORDER BY ordinal_position
        )
        INTO select_list
        FROM information_schema.columns
        WHERE table_schema = 'gold'
          AND table_name = src_view;

        IF select_list IS NULL THEN
            RAISE EXCEPTION 'Source view gold.% not found or has no columns', src_view;
        END IF;

        ddl := format(
            'CREATE OR REPLACE VIEW gold_bi.%I AS SELECT %s FROM gold.%I;',
            src_view,
            E'\n    ' || select_list,
            src_view
        );

        EXECUTE ddl;
        RAISE NOTICE 'Created gold_bi.%', src_view;
    END LOOP;
END $$;

COMMIT;

-- Validation
SELECT
    table_schema,
    table_name,
    COUNT(*) FILTER (WHERE data_type = 'numeric' AND numeric_precision IS NULL) AS unconstrained_numeric_columns,
    COUNT(*) FILTER (WHERE data_type = 'double precision') AS double_precision_columns
FROM information_schema.columns
WHERE table_schema = 'gold_bi'
  AND table_name IN (
      'vw_shift_manufacturing_performance',
      'vw_line_daily_performance',
      'vw_site_daily_performance',
      'vw_site_executive_summary',
      'vw_data_quality_domain_summary',
      'vw_data_quality_rule_status'
  )
GROUP BY table_schema, table_name
ORDER BY table_name;

SELECT 'vw_shift_manufacturing_performance' AS view_name, COUNT(*) AS row_count
FROM gold_bi.vw_shift_manufacturing_performance
UNION ALL
SELECT 'vw_line_daily_performance', COUNT(*)
FROM gold_bi.vw_line_daily_performance
UNION ALL
SELECT 'vw_site_daily_performance', COUNT(*)
FROM gold_bi.vw_site_daily_performance
UNION ALL
SELECT 'vw_site_executive_summary', COUNT(*)
FROM gold_bi.vw_site_executive_summary
UNION ALL
SELECT 'vw_data_quality_domain_summary', COUNT(*)
FROM gold_bi.vw_data_quality_domain_summary
UNION ALL
SELECT 'vw_data_quality_rule_status', COUNT(*)
FROM gold_bi.vw_data_quality_rule_status
ORDER BY view_name;
