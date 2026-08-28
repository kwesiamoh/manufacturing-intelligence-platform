-- Stage 6C.2 — Benchmark electricity-cost analytics.
-- Synthetic enterprise consumption x real external Eurostat price benchmark.

CREATE OR REPLACE VIEW vw_site_shift_electricity_cost_benchmark AS
WITH site_energy AS (
    SELECT
        d.site_energy_detail_id,
        s.site_code,
        s.site_name,
        s.country_code,
        sh.shift_code,
        d.timestamp_start,
        d.timestamp_end,
        d.site_total_electricity_kwh,
        d.production_units,
        CASE
            WHEN EXTRACT(MONTH FROM d.timestamp_start) <= 6
            THEN EXTRACT(YEAR FROM d.timestamp_start)::integer || '-S1'
            ELSE EXTRACT(YEAR FROM d.timestamp_start)::integer || '-S2'
        END AS eurostat_period
    FROM fact_site_energy_detail d
    JOIN dim_site s
      ON s.site_id=d.site_id
    JOIN dim_shift sh
      ON sh.shift_id=d.shift_id
),
price AS (
    SELECT
        geo_code,
        period_code,
        price_value AS benchmark_eur_per_kwh,
        consumption_band_code,
        tax_code,
        currency_code,
        unit_code
    FROM ref_eurostat_electricity_price_observation
    WHERE dataset_code='nrg_pc_205'
      AND consumption_band_code='MWH2000-19999'
      AND tax_code='X_VAT'
      AND currency_code='EUR'
      AND unit_code='KWH'
)
SELECT
    e.*,
    p.benchmark_eur_per_kwh,
    p.consumption_band_code,
    p.tax_code,
    p.currency_code,

    e.site_total_electricity_kwh
      * p.benchmark_eur_per_kwh
        AS benchmark_electricity_cost_eur,

    CASE
        WHEN e.production_units > 0
        THEN (
            e.site_total_electricity_kwh
            * p.benchmark_eur_per_kwh
        ) / e.production_units * 1000.0
    END AS benchmark_electricity_cost_eur_per_1000_units

FROM site_energy e
LEFT JOIN price p
  ON p.geo_code=e.country_code
 AND p.period_code=e.eurostat_period;


CREATE OR REPLACE VIEW vw_site_electricity_cost_summary AS
SELECT
    site_code,
    site_name,
    country_code,

    SUM(site_total_electricity_kwh) AS site_total_electricity_kwh,
    SUM(production_units) AS production_units,
    SUM(benchmark_electricity_cost_eur) AS benchmark_electricity_cost_eur,

    CASE
        WHEN SUM(production_units) > 0
        THEN SUM(benchmark_electricity_cost_eur)
             / SUM(production_units) * 1000.0
    END AS benchmark_electricity_cost_eur_per_1000_units,

    CASE
        WHEN SUM(site_total_electricity_kwh) > 0
        THEN SUM(benchmark_electricity_cost_eur)
             / SUM(site_total_electricity_kwh)
    END AS weighted_benchmark_eur_per_kwh

FROM vw_site_shift_electricity_cost_benchmark
GROUP BY site_code, site_name, country_code;


CREATE OR REPLACE VIEW vw_site_electricity_cost_rank AS
SELECT
    *,
    DENSE_RANK() OVER (
        ORDER BY benchmark_electricity_cost_eur_per_1000_units ASC
    ) AS cost_intensity_rank,

    DENSE_RANK() OVER (
        ORDER BY weighted_benchmark_eur_per_kwh ASC
    ) AS benchmark_price_rank
FROM vw_site_electricity_cost_summary;


CREATE OR REPLACE VIEW vw_country_semester_electricity_price_benchmark AS
SELECT
    geo_code,
    geo_name,
    period_code,
    price_value AS benchmark_eur_per_kwh,
    consumption_band_code,
    consumption_band_label,
    tax_code,
    tax_label,
    currency_code
FROM ref_eurostat_electricity_price_observation
WHERE dataset_code='nrg_pc_205'
  AND consumption_band_code='MWH2000-19999'
  AND tax_code='X_VAT'
  AND currency_code='EUR'
  AND unit_code='KWH';
