\pset pager off

\echo '=== Eurostat selected price rows: expected 24 ==='
SELECT COUNT(*) AS row_count
FROM ref_eurostat_electricity_price_observation
WHERE dataset_code='nrg_pc_205'
  AND consumption_band_code='MWH2000-19999'
  AND tax_code='X_VAT'
  AND currency_code='EUR'
  AND unit_code='KWH';

\echo '=== Country / period coverage ==='
SELECT
    geo_code,
    COUNT(*) AS semester_count,
    MIN(price_value) AS min_eur_per_kwh,
    MAX(price_value) AS max_eur_per_kwh
FROM ref_eurostat_electricity_price_observation
WHERE dataset_code='nrg_pc_205'
  AND consumption_band_code='MWH2000-19999'
  AND tax_code='X_VAT'
  AND currency_code='EUR'
  AND unit_code='KWH'
GROUP BY geo_code
ORDER BY geo_code;

\echo '=== Site-shift benchmark row count: expected 13,158 ==='
SELECT COUNT(*) AS row_count
FROM vw_site_shift_electricity_cost_benchmark;

\echo '=== Missing price matches: expected zero ==='
SELECT COUNT(*) AS bad_rows
FROM vw_site_shift_electricity_cost_benchmark
WHERE benchmark_eur_per_kwh IS NULL;

\echo '=== Invalid price / cost values: expected all zero ==='
SELECT
    COUNT(*) FILTER (WHERE benchmark_eur_per_kwh <= 0) AS bad_price,
    COUNT(*) FILTER (WHERE benchmark_electricity_cost_eur <= 0) AS bad_cost,
    COUNT(*) FILTER (
        WHERE benchmark_electricity_cost_eur_per_1000_units <= 0
    ) AS bad_cost_intensity
FROM vw_site_shift_electricity_cost_benchmark;

\echo '=== Site annual-consumption-band check ==='
WITH annual AS (
    SELECT
        site_code,
        EXTRACT(YEAR FROM timestamp_start)::integer AS year,
        SUM(site_total_electricity_kwh) / 1000.0 AS annual_mwh
    FROM vw_site_shift_electricity_cost_benchmark
    GROUP BY
        site_code,
        EXTRACT(YEAR FROM timestamp_start)::integer
)
SELECT
    site_code,
    year,
    ROUND(annual_mwh::numeric, 1) AS annual_mwh,
    CASE
        WHEN annual_mwh >= 2000 AND annual_mwh < 20000
        THEN 'PASS'
        ELSE 'FAIL'
    END AS band_check
FROM annual
ORDER BY site_code, year;

\echo '=== Annual band failures: expected zero ==='
WITH annual AS (
    SELECT
        site_code,
        EXTRACT(YEAR FROM timestamp_start)::integer AS year,
        SUM(site_total_electricity_kwh) / 1000.0 AS annual_mwh
    FROM vw_site_shift_electricity_cost_benchmark
    GROUP BY
        site_code,
        EXTRACT(YEAR FROM timestamp_start)::integer
)
SELECT COUNT(*) AS bad_rows
FROM annual
WHERE annual_mwh < 2000 OR annual_mwh >= 20000;

\echo '=== Benchmark cost reconciliation: expected zero ==='
SELECT COUNT(*) AS bad_rows
FROM vw_site_shift_electricity_cost_benchmark
WHERE ABS(
    benchmark_electricity_cost_eur
    - site_total_electricity_kwh * benchmark_eur_per_kwh
) > 0.01;

\echo '=== Site benchmark electricity-cost ranking ==='
SELECT
    site_code,
    country_code,
    ROUND(site_total_electricity_kwh::numeric, 0) AS electricity_kwh,
    ROUND(weighted_benchmark_eur_per_kwh::numeric, 5) AS weighted_eur_per_kwh,
    ROUND(benchmark_electricity_cost_eur::numeric, 2) AS benchmark_cost_eur,
    ROUND(
        benchmark_electricity_cost_eur_per_1000_units::numeric,
        4
    ) AS eur_per_1000_units,
    cost_intensity_rank
FROM vw_site_electricity_cost_rank
ORDER BY cost_intensity_rank;

\echo '=== Mandatory energy-cost gate ==='
DO $validation$
DECLARE
    selected_price_count bigint;
    bad_count bigint;
BEGIN
    SELECT COUNT(*) INTO selected_price_count
    FROM ref_eurostat_electricity_price_observation
    WHERE dataset_code = 'nrg_pc_205'
      AND consumption_band_code = 'MWH2000-19999'
      AND tax_code = 'X_VAT'
      AND currency_code = 'EUR'
      AND unit_code = 'KWH';
    IF selected_price_count <> 24 THEN
        RAISE EXCEPTION 'energy-cost selected Eurostat price population has % rows; expected 24',
            selected_price_count;
    END IF;

    SELECT COUNT(*) INTO bad_count
    FROM (
        SELECT geo_code
        FROM ref_eurostat_electricity_price_observation
        WHERE dataset_code = 'nrg_pc_205'
          AND consumption_band_code = 'MWH2000-19999'
          AND tax_code = 'X_VAT'
          AND currency_code = 'EUR'
          AND unit_code = 'KWH'
        GROUP BY geo_code
        HAVING COUNT(*) <> 4 OR MIN(price_value) <= 0
    ) x;
    IF bad_count <> 0 OR (
        SELECT COUNT(DISTINCT geo_code)
        FROM ref_eurostat_electricity_price_observation
        WHERE dataset_code = 'nrg_pc_205'
          AND consumption_band_code = 'MWH2000-19999'
          AND tax_code = 'X_VAT'
          AND currency_code = 'EUR'
          AND unit_code = 'KWH'
    ) <> 6 THEN
        RAISE EXCEPTION 'energy-cost Eurostat country/semester coverage is incomplete';
    END IF;

    IF (SELECT COUNT(*) FROM vw_site_shift_electricity_cost_benchmark) <> 13158 THEN
        RAISE EXCEPTION 'energy-cost site-shift benchmark does not contain 13,158 rows';
    END IF;

    SELECT COUNT(*) INTO bad_count
    FROM vw_site_shift_electricity_cost_benchmark
    WHERE benchmark_eur_per_kwh IS NULL OR benchmark_eur_per_kwh <= 0
       OR benchmark_electricity_cost_eur <= 0
       OR benchmark_electricity_cost_eur_per_1000_units <= 0
       OR ABS(benchmark_electricity_cost_eur
              - site_total_electricity_kwh * benchmark_eur_per_kwh) > 0.01;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'energy-cost cost gate found % missing, invalid, or unreconciled rows', bad_count;
    END IF;

    SELECT COUNT(*) INTO bad_count
    FROM (
        SELECT site_code, EXTRACT(YEAR FROM timestamp_start)::integer AS year,
               SUM(site_total_electricity_kwh) / 1000.0 AS annual_mwh
        FROM vw_site_shift_electricity_cost_benchmark
        GROUP BY site_code, EXTRACT(YEAR FROM timestamp_start)::integer
    ) annual
    WHERE annual_mwh < 2000 OR annual_mwh >= 20000;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'energy-cost annual consumption-band gate found % site-years outside the selected band',
            bad_count;
    END IF;
END
$validation$;
