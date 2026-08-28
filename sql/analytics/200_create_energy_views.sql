-- Stage 6A — Electricity performance and energy-intensity analytics
-- Uses validated synthetic enterprise line-level electricity facts.

CREATE OR REPLACE VIEW vw_shift_energy_kpi AS
WITH src AS (
    SELECT source_dataset_id
    FROM dim_source_dataset
    WHERE source_code = 'SYNTHETIC_ENTERPRISE'
),
elec AS (
    SELECT
        e.energy_id,
        e.source_record_id AS energy_record_id,
        e.production_record_id,
        e.timestamp,
        e.date_id,
        s.site_code,
        s.site_name,
        l.line_code,
        l.line_name,
        e.consumption AS electricity_kwh,
        e.demand AS avg_demand_kw
    FROM fact_energy e
    JOIN src x
      ON x.source_dataset_id = e.source_dataset_id
    JOIN dim_site s
      ON s.site_id = e.site_id
    JOIN dim_line l
      ON l.line_id = e.line_id
    JOIN dim_utility u
      ON u.utility_id = e.utility_id
    WHERE u.utility_code = 'ELECTRICITY'
),
prod AS (
    SELECT
        production_record_id,
        product_code,
        product_name,
        shift_code,
        shift_name,
        actual_quantity,
        good_quantity,
        reject_quantity,
        operating_time_min,
        planned_production_time_min,
        oee,
        production_attainment
    FROM vw_shift_production_kpi
)
SELECT
    e.*,
    p.product_code,
    p.product_name,
    p.shift_code,
    p.shift_name,
    p.actual_quantity,
    p.good_quantity,
    p.reject_quantity,
    p.operating_time_min,
    p.planned_production_time_min,
    p.oee,
    p.production_attainment,

    CASE
        WHEN p.actual_quantity > 0
        THEN e.electricity_kwh / p.actual_quantity * 1000.0
    END AS kwh_per_1000_actual_units,

    CASE
        WHEN p.good_quantity > 0
        THEN e.electricity_kwh / p.good_quantity * 1000.0
    END AS kwh_per_1000_good_units,

    CASE
        WHEN p.operating_time_min > 0
        THEN e.electricity_kwh / (p.operating_time_min / 60.0)
    END AS kwh_per_operating_hour,

    CASE
        WHEN p.planned_production_time_min > 0
        THEN e.electricity_kwh / (p.planned_production_time_min / 60.0)
    END AS kwh_per_planned_hour

FROM elec e
JOIN prod p
  ON p.production_record_id = e.production_record_id;


CREATE OR REPLACE VIEW vw_line_daily_energy_kpi AS
SELECT
    date_id,
    site_code,
    site_name,
    line_code,
    line_name,

    SUM(electricity_kwh) AS electricity_kwh,
    AVG(avg_demand_kw) AS avg_demand_kw,

    SUM(actual_quantity) AS actual_quantity,
    SUM(good_quantity) AS good_quantity,
    SUM(reject_quantity) AS reject_quantity,
    SUM(operating_time_min) AS operating_time_min,
    SUM(planned_production_time_min) AS planned_production_time_min,

    CASE
        WHEN SUM(actual_quantity) > 0
        THEN SUM(electricity_kwh) / SUM(actual_quantity) * 1000.0
    END AS kwh_per_1000_actual_units,

    CASE
        WHEN SUM(good_quantity) > 0
        THEN SUM(electricity_kwh) / SUM(good_quantity) * 1000.0
    END AS kwh_per_1000_good_units,

    CASE
        WHEN SUM(operating_time_min) > 0
        THEN SUM(electricity_kwh) / (SUM(operating_time_min) / 60.0)
    END AS kwh_per_operating_hour,

    CASE
        WHEN SUM(planned_production_time_min) > 0
        THEN SUM(electricity_kwh) / (SUM(planned_production_time_min) / 60.0)
    END AS kwh_per_planned_hour

FROM vw_shift_energy_kpi
GROUP BY
    date_id,
    site_code,
    site_name,
    line_code,
    line_name;


CREATE OR REPLACE VIEW vw_site_daily_energy_kpi AS
SELECT
    date_id,
    site_code,
    site_name,

    SUM(electricity_kwh) AS electricity_kwh,
    AVG(avg_demand_kw) AS avg_line_demand_kw,

    SUM(actual_quantity) AS actual_quantity,
    SUM(good_quantity) AS good_quantity,
    SUM(reject_quantity) AS reject_quantity,
    SUM(operating_time_min) AS operating_time_min,
    SUM(planned_production_time_min) AS planned_production_time_min,

    CASE
        WHEN SUM(actual_quantity) > 0
        THEN SUM(electricity_kwh) / SUM(actual_quantity) * 1000.0
    END AS kwh_per_1000_actual_units,

    CASE
        WHEN SUM(good_quantity) > 0
        THEN SUM(electricity_kwh) / SUM(good_quantity) * 1000.0
    END AS kwh_per_1000_good_units,

    CASE
        WHEN SUM(operating_time_min) > 0
        THEN SUM(electricity_kwh) / (SUM(operating_time_min) / 60.0)
    END AS kwh_per_operating_hour,

    CASE
        WHEN SUM(planned_production_time_min) > 0
        THEN SUM(electricity_kwh) / (SUM(planned_production_time_min) / 60.0)
    END AS kwh_per_planned_hour

FROM vw_shift_energy_kpi
GROUP BY
    date_id,
    site_code,
    site_name;


CREATE OR REPLACE VIEW vw_line_energy_summary AS
SELECT
    site_code,
    site_name,
    line_code,
    line_name,

    COUNT(*) AS shift_count,
    SUM(electricity_kwh) AS electricity_kwh,
    AVG(avg_demand_kw) AS avg_demand_kw,

    SUM(actual_quantity) AS actual_quantity,
    SUM(good_quantity) AS good_quantity,
    SUM(reject_quantity) AS reject_quantity,
    SUM(operating_time_min) AS operating_time_min,
    SUM(planned_production_time_min) AS planned_production_time_min,

    CASE
        WHEN SUM(actual_quantity) > 0
        THEN SUM(electricity_kwh) / SUM(actual_quantity) * 1000.0
    END AS kwh_per_1000_actual_units,

    CASE
        WHEN SUM(good_quantity) > 0
        THEN SUM(electricity_kwh) / SUM(good_quantity) * 1000.0
    END AS kwh_per_1000_good_units,

    CASE
        WHEN SUM(operating_time_min) > 0
        THEN SUM(electricity_kwh) / (SUM(operating_time_min) / 60.0)
    END AS kwh_per_operating_hour,

    CASE
        WHEN SUM(planned_production_time_min) > 0
        THEN SUM(electricity_kwh) / (SUM(planned_production_time_min) / 60.0)
    END AS kwh_per_planned_hour

FROM vw_shift_energy_kpi
GROUP BY
    site_code,
    site_name,
    line_code,
    line_name;


CREATE OR REPLACE VIEW vw_line_energy_rank AS
SELECT
    *,
    DENSE_RANK() OVER (
        ORDER BY kwh_per_1000_good_units ASC
    ) AS enterprise_energy_intensity_rank,

    DENSE_RANK() OVER (
        PARTITION BY site_code
        ORDER BY kwh_per_1000_good_units ASC
    ) AS site_energy_intensity_rank
FROM vw_line_energy_summary;


CREATE OR REPLACE VIEW vw_site_energy_summary AS
SELECT
    site_code,
    site_name,
    COUNT(*) AS line_count,

    SUM(electricity_kwh) AS electricity_kwh,
    SUM(actual_quantity) AS actual_quantity,
    SUM(good_quantity) AS good_quantity,
    SUM(reject_quantity) AS reject_quantity,

    CASE
        WHEN SUM(actual_quantity) > 0
        THEN SUM(electricity_kwh) / SUM(actual_quantity) * 1000.0
    END AS kwh_per_1000_actual_units,

    CASE
        WHEN SUM(good_quantity) > 0
        THEN SUM(electricity_kwh) / SUM(good_quantity) * 1000.0
    END AS kwh_per_1000_good_units

FROM vw_line_energy_summary
GROUP BY
    site_code,
    site_name;


CREATE OR REPLACE VIEW vw_site_energy_rank AS
SELECT
    *,
    DENSE_RANK() OVER (
        ORDER BY kwh_per_1000_good_units ASC
    ) AS energy_intensity_rank
FROM vw_site_energy_summary;
