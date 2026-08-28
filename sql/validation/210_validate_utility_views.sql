\pset pager off

\echo '=== Stage 6B detail-table counts ==='
SELECT 'fact_line_energy_detail' AS object_name, COUNT(*) AS row_count
FROM fact_line_energy_detail
UNION ALL
SELECT 'fact_site_energy_detail', COUNT(*)
FROM fact_site_energy_detail
UNION ALL
SELECT 'vw_shift_energy_detail_kpi', COUNT(*)
FROM vw_shift_energy_detail_kpi
UNION ALL
SELECT 'vw_site_auxiliary_energy_kpi', COUNT(*)
FROM vw_site_auxiliary_energy_kpi
UNION ALL
SELECT 'vw_line_idle_energy_summary', COUNT(*)
FROM vw_line_idle_energy_summary
UNION ALL
SELECT 'vw_compressed_air_line_summary', COUNT(*)
FROM vw_compressed_air_line_summary
UNION ALL
SELECT 'vw_site_auxiliary_summary', COUNT(*)
FROM vw_site_auxiliary_summary;

\echo '=== Line electricity reconciliation: expected zero ==='
SELECT COUNT(*) AS bad_rows
FROM fact_line_energy_detail
WHERE ABS(
    line_total_electricity_kwh
    - (line_production_electricity_kwh + line_idle_electricity_kwh)
) > 0.001;

\echo '=== Site electricity reconciliation: expected zero ==='
SELECT COUNT(*) AS bad_rows
FROM fact_site_energy_detail
WHERE ABS(
    site_total_electricity_kwh
    - (line_electricity_kwh + site_auxiliary_electricity_kwh)
) > 0.001;

\echo '=== Auxiliary power reconciliation: expected zero ==='
SELECT COUNT(*) AS bad_rows
FROM fact_site_energy_detail
WHERE ABS(
    site_auxiliary_electricity_kwh
    - ((site_auxiliary_base_kw + site_weather_auxiliary_kw) * shift_hours)
) > 0.001;

\echo '=== Idle share bounds: expected zero ==='
SELECT COUNT(*) AS bad_rows
FROM vw_shift_energy_detail_kpi
WHERE idle_energy_share < 0 OR idle_energy_share > 1.000001;

\echo '=== Auxiliary share bounds: expected zero ==='
SELECT COUNT(*) AS bad_rows
FROM vw_site_auxiliary_energy_kpi
WHERE auxiliary_energy_share < 0 OR auxiliary_energy_share > 1.000001
   OR weather_sensitive_aux_power_share < 0
   OR weather_sensitive_aux_power_share > 1.000001;

\echo '=== Compressed-air coverage by product ==='
SELECT
    product_code,
    COUNT(*) AS shifts,
    COUNT(compressed_air_nm3) AS modelled_shifts,
    COUNT(*) - COUNT(compressed_air_nm3) AS unmodelled_shifts,
    ROUND(
        100.0 * COUNT(compressed_air_nm3) / COUNT(*),
        2
    ) AS coverage_pct
FROM vw_shift_energy_detail_kpi
GROUP BY product_code
ORDER BY product_code;

\echo '=== Negative compressed-air values: expected zero ==='
SELECT COUNT(*) AS bad_rows
FROM vw_shift_energy_detail_kpi
WHERE compressed_air_nm3 < 0
   OR compressed_air_nm3_per_1000_units < 0;

\echo '=== Site auxiliary / total-energy ranking ==='
SELECT
    site_code,
    ROUND(site_total_electricity_kwh::numeric, 0) AS total_site_electricity_kwh,
    ROUND((auxiliary_energy_share * 100)::numeric, 2) AS auxiliary_energy_pct,
    ROUND(total_site_kwh_per_1000_units::numeric, 4) AS total_site_kwh_per_1000_units,
    total_site_energy_intensity_rank
FROM vw_site_auxiliary_rank
ORDER BY total_site_energy_intensity_rank;

\echo '=== Compressed-air line/product summary ==='
SELECT
    site_code,
    line_code,
    product_code,
    modelled_shift_count,
    ROUND(compressed_air_nm3::numeric, 0) AS compressed_air_nm3,
    ROUND(compressed_air_nm3_per_1000_units::numeric, 4) AS nm3_per_1000_units
FROM vw_compressed_air_line_summary
WHERE modelled_shift_count > 0
ORDER BY site_code, line_code, product_code;

\echo '=== Mandatory Stage 6B gate ==='
DO $validation$
DECLARE
    bad_count bigint;
BEGIN
    IF (SELECT COUNT(*) FROM fact_line_energy_detail) <> 65790
       OR (SELECT COUNT(*) FROM fact_site_energy_detail) <> 13158
       OR (SELECT COUNT(*) FROM vw_shift_energy_detail_kpi) <> 65790
       OR (SELECT COUNT(*) FROM vw_site_auxiliary_energy_kpi) <> 13158
       OR NOT EXISTS (SELECT 1 FROM vw_line_idle_energy_summary)
       OR NOT EXISTS (SELECT 1 FROM vw_compressed_air_line_summary)
       OR (SELECT COUNT(*) FROM vw_site_auxiliary_summary) <> 6 THEN
        RAISE EXCEPTION 'Stage 6B detail and utility views have incomplete canonical coverage';
    END IF;

    SELECT SUM(n) INTO bad_count
    FROM (
        SELECT COUNT(*) AS n FROM fact_line_energy_detail
        WHERE ABS(line_total_electricity_kwh
                  - line_production_electricity_kwh
                  - line_idle_electricity_kwh) > 0.001
        UNION ALL SELECT COUNT(*) FROM fact_site_energy_detail
        WHERE ABS(site_total_electricity_kwh
                  - line_electricity_kwh
                  - site_auxiliary_electricity_kwh) > 0.001
        UNION ALL SELECT COUNT(*) FROM fact_site_energy_detail
        WHERE ABS(site_auxiliary_electricity_kwh
                  - (site_auxiliary_base_kw + site_weather_auxiliary_kw)
                    * shift_hours) > 0.001
        UNION ALL SELECT COUNT(*) FROM vw_shift_energy_detail_kpi
        WHERE idle_energy_share < 0 OR idle_energy_share > 1.000001
           OR compressed_air_nm3 < 0 OR compressed_air_nm3_per_1000_units < 0
        UNION ALL SELECT COUNT(*) FROM vw_site_auxiliary_energy_kpi
        WHERE auxiliary_energy_share < 0 OR auxiliary_energy_share > 1.000001
           OR weather_sensitive_aux_power_share < 0
           OR weather_sensitive_aux_power_share > 1.000001
    ) checks;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'Stage 6B utility gate found % invalid or unreconciled rows', bad_count;
    END IF;
END
$validation$;
