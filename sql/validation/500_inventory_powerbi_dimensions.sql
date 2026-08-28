\pset pager off

\echo '=== Stage 11A Power BI dimension inventory ==='

SELECT
    c.table_name,
    c.ordinal_position,
    c.column_name,
    c.data_type
FROM information_schema.columns c
WHERE c.table_schema = 'public'
  AND c.table_name IN (
      'dim_site',
      'dim_line',
      'dim_product',
      'dim_shift',
      'dim_time'
  )
ORDER BY c.table_name, c.ordinal_position;

\echo ''
\echo '=== Dimension row counts ==='

SELECT 'dim_site' AS object_name, COUNT(*) AS row_count FROM public.dim_site
UNION ALL
SELECT 'dim_line', COUNT(*) FROM public.dim_line
UNION ALL
SELECT 'dim_product', COUNT(*) FROM public.dim_product
UNION ALL
SELECT 'dim_shift', COUNT(*) FROM public.dim_shift
UNION ALL
SELECT 'dim_time', COUNT(*) FROM public.dim_time
ORDER BY object_name;

\echo ''
\echo '=== Candidate key uniqueness checks ==='

SELECT
    COUNT(*) AS rows,
    COUNT(DISTINCT site_code) AS distinct_site_codes
FROM public.dim_site;

SELECT
    COUNT(*) AS rows,
    COUNT(DISTINCT line_code) AS distinct_line_codes
FROM public.dim_line;

SELECT
    COUNT(*) AS rows,
    COUNT(DISTINCT product_code) AS distinct_product_codes
FROM public.dim_product;

SELECT
    COUNT(*) AS rows,
    COUNT(DISTINCT shift_code) AS distinct_shift_codes
FROM public.dim_shift;

SELECT
    COUNT(*) AS rows,
    COUNT(DISTINCT date_id) AS distinct_date_ids
FROM public.dim_time;
