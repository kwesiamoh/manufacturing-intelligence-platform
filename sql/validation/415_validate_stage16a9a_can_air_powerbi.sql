\pset pager off

-- Stage 16A.9A targeted propagation gate.
-- This validates the amended can-line compressed-air field at the loaded fact,
-- Gold, and Power BI compatibility layers without changing any view logic.

\echo '=== Stage 16A.9A can-line compressed-air propagation ==='
SELECT
    layer_name,
    row_count,
    null_air_rows,
    distinct_intensities,
    compressed_air_nm3
FROM (
    SELECT
        'public.fact_line_energy_detail'::text AS layer_name,
        COUNT(*)::bigint AS row_count,
        COUNT(*) FILTER (WHERE f.compressed_air_nm3 IS NULL
                           OR f.compressed_air_nm3_per_1000_units IS NULL)::bigint
            AS null_air_rows,
        COUNT(DISTINCT f.compressed_air_nm3_per_1000_units)::bigint
            AS distinct_intensities,
        SUM(f.compressed_air_nm3)::double precision AS compressed_air_nm3
    FROM public.fact_line_energy_detail f
    JOIN public.dim_line l ON l.line_id = f.line_id
    WHERE l.line_type = 'CAN_ENERGY_250'

    UNION ALL

    SELECT
        'gold.vw_shift_manufacturing_performance',
        COUNT(*),
        COUNT(*) FILTER (WHERE g.compressed_air_nm3 IS NULL
                           OR g.compressed_air_nm3_per_1000_units IS NULL),
        COUNT(DISTINCT g.compressed_air_nm3_per_1000_units),
        SUM(g.compressed_air_nm3)::double precision
    FROM gold.vw_shift_manufacturing_performance g
    JOIN public.dim_site s ON s.site_code = g.site_code
    JOIN public.dim_line l ON l.site_id = s.site_id AND l.line_code = g.line_code
    WHERE l.line_type = 'CAN_ENERGY_250'

    UNION ALL

    SELECT
        'gold_bi.vw_shift_manufacturing_performance',
        COUNT(*),
        COUNT(*) FILTER (WHERE g.compressed_air_nm3 IS NULL
                           OR g.compressed_air_nm3_per_1000_units IS NULL),
        COUNT(DISTINCT g.compressed_air_nm3_per_1000_units),
        SUM(g.compressed_air_nm3)::double precision
    FROM gold_bi.vw_shift_manufacturing_performance g
    JOIN public.dim_site s ON s.site_code = g.site_code
    JOIN public.dim_line l ON l.site_id = s.site_id AND l.line_code = g.line_code
    WHERE l.line_type = 'CAN_ENERGY_250'
) checks
ORDER BY layer_name;

\echo '=== Mandatory Stage 16A.9A propagation gate ==='
DO $validation$
DECLARE
    layer_record record;
    formula_bad_rows bigint;
BEGIN
    FOR layer_record IN
        SELECT *
        FROM (
            SELECT
                'public.fact_line_energy_detail'::text AS layer_name,
                COUNT(*)::bigint AS row_count,
                COUNT(*) FILTER (WHERE f.compressed_air_nm3 IS NULL
                                   OR f.compressed_air_nm3_per_1000_units IS NULL)::bigint
                    AS null_air_rows,
                COUNT(*) FILTER (
                    WHERE ABS(f.compressed_air_nm3_per_1000_units - 5.0) > 0.000000001
                )::bigint AS wrong_intensity_rows,
                SUM(f.compressed_air_nm3)::double precision AS compressed_air_nm3
            FROM public.fact_line_energy_detail f
            JOIN public.dim_line l ON l.line_id = f.line_id
            WHERE l.line_type = 'CAN_ENERGY_250'

            UNION ALL

            SELECT
                'gold.vw_shift_manufacturing_performance',
                COUNT(*),
                COUNT(*) FILTER (WHERE g.compressed_air_nm3 IS NULL
                                   OR g.compressed_air_nm3_per_1000_units IS NULL),
                COUNT(*) FILTER (
                    WHERE ABS(g.compressed_air_nm3_per_1000_units - 5.0) > 0.000000001
                ),
                SUM(g.compressed_air_nm3)::double precision
            FROM gold.vw_shift_manufacturing_performance g
            JOIN public.dim_site s ON s.site_code = g.site_code
            JOIN public.dim_line l ON l.site_id = s.site_id AND l.line_code = g.line_code
            WHERE l.line_type = 'CAN_ENERGY_250'

            UNION ALL

            SELECT
                'gold_bi.vw_shift_manufacturing_performance',
                COUNT(*),
                COUNT(*) FILTER (WHERE g.compressed_air_nm3 IS NULL
                                   OR g.compressed_air_nm3_per_1000_units IS NULL),
                COUNT(*) FILTER (
                    WHERE ABS(g.compressed_air_nm3_per_1000_units - 5.0) > 0.000000001
                ),
                SUM(g.compressed_air_nm3)::double precision
            FROM gold_bi.vw_shift_manufacturing_performance g
            JOIN public.dim_site s ON s.site_code = g.site_code
            JOIN public.dim_line l ON l.site_id = s.site_id AND l.line_code = g.line_code
            WHERE l.line_type = 'CAN_ENERGY_250'
        ) layer_checks
    LOOP
        IF layer_record.row_count <> 6579
           OR layer_record.null_air_rows <> 0
           OR layer_record.wrong_intensity_rows <> 0
           OR ABS(layer_record.compressed_air_nm3 - 12805152.250) > 0.001 THEN
            RAISE EXCEPTION
                'Stage 16A.9A failed at %: rows %, nulls %, wrong intensity %, total %',
                layer_record.layer_name,
                layer_record.row_count,
                layer_record.null_air_rows,
                layer_record.wrong_intensity_rows,
                layer_record.compressed_air_nm3;
        END IF;
    END LOOP;

    SELECT COUNT(*) INTO formula_bad_rows
    FROM public.fact_line_energy_detail f
    JOIN public.dim_line l ON l.line_id = f.line_id
    WHERE l.line_type = 'CAN_ENERGY_250'
      AND ABS(f.compressed_air_nm3 - (5.0 * f.actual_quantity / 1000.0)) > 0.000001;

    IF formula_bad_rows <> 0 THEN
        RAISE EXCEPTION
            'Stage 16A.9A found % can-line rows that do not satisfy the generic utility formula',
            formula_bad_rows;
    END IF;
END
$validation$;
