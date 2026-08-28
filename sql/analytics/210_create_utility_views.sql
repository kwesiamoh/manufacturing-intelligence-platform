-- Stage 6B — Idle energy, auxiliary/weather energy and compressed-air analytics.

CREATE OR REPLACE VIEW vw_shift_energy_detail_kpi AS
SELECT
    d.energy_record_id,
    d.production_record_id,
    s.site_code,
    s.site_name,
    l.line_code,
    l.line_name,
    p.product_code,
    p.product_name,
    sh.shift_code,
    d.timestamp_start,
    d.timestamp_end,
    d.actual_quantity,

    d.line_production_electricity_kwh,
    d.line_idle_electricity_kwh,
    d.line_total_electricity_kwh,

    CASE
        WHEN d.line_total_electricity_kwh > 0
        THEN d.line_idle_electricity_kwh / d.line_total_electricity_kwh
    END AS idle_energy_share,

    CASE
        WHEN d.actual_quantity > 0
        THEN d.line_idle_electricity_kwh / d.actual_quantity * 1000.0
    END AS idle_kwh_per_1000_units,

    d.compressed_air_nm3,
    d.compressed_air_nm3_per_1000_units,

    d.shift_mean_air_temperature_c,
    d.site_auxiliary_base_kw,
    d.site_weather_auxiliary_kw

FROM fact_line_energy_detail d
JOIN dim_site s ON s.site_id=d.site_id
JOIN dim_line l ON l.line_id=d.line_id
JOIN dim_product p ON p.product_id=d.product_id
JOIN dim_shift sh ON sh.shift_id=d.shift_id;


CREATE OR REPLACE VIEW vw_site_auxiliary_energy_kpi AS
SELECT
    d.site_energy_record_id,
    s.site_code,
    s.site_name,
    sh.shift_code,
    d.timestamp_start,
    d.timestamp_end,
    d.line_electricity_kwh,
    d.site_auxiliary_electricity_kwh,
    d.site_total_electricity_kwh,
    d.production_units,
    d.mean_air_temperature_c,
    d.site_auxiliary_base_kw,
    d.site_weather_auxiliary_kw,

    CASE
        WHEN d.site_total_electricity_kwh > 0
        THEN d.site_auxiliary_electricity_kwh / d.site_total_electricity_kwh
    END AS auxiliary_energy_share,

    CASE
        WHEN (d.site_auxiliary_base_kw + d.site_weather_auxiliary_kw) > 0
        THEN d.site_weather_auxiliary_kw /
             (d.site_auxiliary_base_kw + d.site_weather_auxiliary_kw)
    END AS weather_sensitive_aux_power_share,

    CASE
        WHEN d.production_units > 0
        THEN d.site_auxiliary_electricity_kwh / d.production_units * 1000.0
    END AS auxiliary_kwh_per_1000_units,

    CASE
        WHEN d.production_units > 0
        THEN d.site_total_electricity_kwh / d.production_units * 1000.0
    END AS total_site_kwh_per_1000_units

FROM fact_site_energy_detail d
JOIN dim_site s ON s.site_id=d.site_id
JOIN dim_shift sh ON sh.shift_id=d.shift_id;


CREATE OR REPLACE VIEW vw_line_idle_energy_summary AS
SELECT
    site_code,
    site_name,
    line_code,
    line_name,

    SUM(line_production_electricity_kwh) AS production_electricity_kwh,
    SUM(line_idle_electricity_kwh) AS idle_electricity_kwh,
    SUM(line_total_electricity_kwh) AS total_electricity_kwh,

    CASE
        WHEN SUM(line_total_electricity_kwh) > 0
        THEN SUM(line_idle_electricity_kwh) / SUM(line_total_electricity_kwh)
    END AS idle_energy_share,

    CASE
        WHEN SUM(actual_quantity) > 0
        THEN SUM(line_idle_electricity_kwh) / SUM(actual_quantity) * 1000.0
    END AS idle_kwh_per_1000_units

FROM vw_shift_energy_detail_kpi
GROUP BY site_code, site_name, line_code, line_name;


CREATE OR REPLACE VIEW vw_compressed_air_line_summary AS
SELECT
    site_code,
    site_name,
    line_code,
    line_name,
    product_code,
    product_name,

    COUNT(*) FILTER (WHERE compressed_air_nm3 IS NOT NULL) AS modelled_shift_count,
    SUM(compressed_air_nm3) AS compressed_air_nm3,
    SUM(actual_quantity) FILTER (WHERE compressed_air_nm3 IS NOT NULL) AS modelled_actual_units,

    CASE
        WHEN SUM(actual_quantity) FILTER (WHERE compressed_air_nm3 IS NOT NULL) > 0
        THEN
            SUM(compressed_air_nm3)
            /
            (SUM(actual_quantity) FILTER (WHERE compressed_air_nm3 IS NOT NULL))
            * 1000.0
    END AS compressed_air_nm3_per_1000_units

FROM vw_shift_energy_detail_kpi
GROUP BY
    site_code, site_name, line_code, line_name, product_code, product_name;


CREATE OR REPLACE VIEW vw_site_auxiliary_summary AS
SELECT
    site_code,
    site_name,

    SUM(line_electricity_kwh) AS line_electricity_kwh,
    SUM(site_auxiliary_electricity_kwh) AS site_auxiliary_electricity_kwh,
    SUM(site_total_electricity_kwh) AS site_total_electricity_kwh,
    SUM(production_units) AS production_units,

    CASE
        WHEN SUM(site_total_electricity_kwh) > 0
        THEN SUM(site_auxiliary_electricity_kwh) / SUM(site_total_electricity_kwh)
    END AS auxiliary_energy_share,

    CASE
        WHEN SUM(production_units) > 0
        THEN SUM(site_total_electricity_kwh) / SUM(production_units) * 1000.0
    END AS total_site_kwh_per_1000_units,

    AVG(mean_air_temperature_c) AS mean_air_temperature_c,
    AVG(site_auxiliary_base_kw) AS avg_auxiliary_base_kw,
    AVG(site_weather_auxiliary_kw) AS avg_weather_auxiliary_kw

FROM vw_site_auxiliary_energy_kpi
GROUP BY site_code, site_name;


CREATE OR REPLACE VIEW vw_site_auxiliary_rank AS
SELECT
    *,
    DENSE_RANK() OVER (
        ORDER BY total_site_kwh_per_1000_units ASC
    ) AS total_site_energy_intensity_rank,

    DENSE_RANK() OVER (
        ORDER BY auxiliary_energy_share ASC
    ) AS auxiliary_share_rank
FROM vw_site_auxiliary_summary;
