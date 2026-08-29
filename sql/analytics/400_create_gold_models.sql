\pset pager off

CREATE SCHEMA IF NOT EXISTS gold;

-- ============================================================
-- 1. Shift-grain integrated operations + loss + energy model
-- Grain: one row per production_record_id / line / shift
-- Expected rows: 65,790
-- ============================================================
CREATE OR REPLACE VIEW gold.vw_shift_manufacturing_performance AS
SELECT
    l.production_id,
    l.production_record_id,
    l.timestamp_start,
    l.timestamp_end,
    l.date_id,
    l.site_code,
    l.site_name,
    l.line_code,
    l.line_name,
    l.product_code,
    l.product_name,
    l.shift_code,
    l.shift_name,

    -- Production
    l.planned_quantity,
    l.actual_quantity,
    l.good_quantity,
    l.reject_quantity,
    l.nominal_rate,
    l.actual_rate,
    l.operating_time_min,
    l.planned_production_time_min,
    l.availability,
    l.performance,
    l.quality,
    l.oee,
    l.production_attainment,
    l.good_output_attainment,
    l.scheduled_throughput_per_hour,
    l.running_throughput_per_hour,
    l.reject_rate,

    -- Downtime / technical losses
    l.planned_downtime_min,
    l.unplanned_downtime_min,
    l.changeover_downtime_min,
    l.theoretical_capacity_units,
    l.operating_capacity_units,
    l.availability_loss_units_exact AS availability_loss_units,
    l.planned_downtime_loss_units_exact AS planned_downtime_loss_units,
    l.unplanned_downtime_loss_units_exact AS unplanned_downtime_loss_units,
    l.changeover_loss_units_subset,
    l.performance_loss_units_exact AS performance_loss_units,
    l.quality_loss_units_exact AS quality_loss_units,
    l.total_technical_loss_units,
    l.plan_shortfall_units,
    l.technical_output_efficiency,

    -- Financial opportunity estimates
    l.standard_loss_value_eur_per_unit,
    l.value_basis,
    l.assumption_class,
    l.planned_downtime_opportunity_eur,
    l.unplanned_downtime_opportunity_eur,
    l.changeover_opportunity_eur_subset,
    l.performance_opportunity_eur,
    l.quality_opportunity_eur,
    l.total_technical_opportunity_eur,
    l.plan_shortfall_opportunity_eur,

    -- Line electricity KPIs
    e.electricity_kwh,
    e.avg_demand_kw,
    e.kwh_per_1000_actual_units,
    e.kwh_per_1000_good_units,
    e.kwh_per_operating_hour,
    e.kwh_per_planned_hour,

    -- Detailed line utility / idle-energy KPIs
    d.line_production_electricity_kwh,
    d.line_idle_electricity_kwh,
    d.line_total_electricity_kwh,
    d.idle_energy_share,
    d.idle_kwh_per_1000_units,
    d.compressed_air_nm3,
    d.compressed_air_nm3_per_1000_units,
    d.shift_mean_air_temperature_c,
    d.site_auxiliary_base_kw,
    d.site_weather_auxiliary_kw

FROM public.vw_shift_loss_accounting l
LEFT JOIN public.vw_shift_energy_kpi e
    ON e.production_record_id = l.production_record_id
LEFT JOIN public.vw_shift_energy_detail_kpi d
    ON d.production_record_id = l.production_record_id;


-- ============================================================
-- 2. Line-day integrated Gold model
-- Grain: one row per date_id / site / line
-- Expected rows: 21,930
-- ============================================================
CREATE OR REPLACE VIEW gold.vw_line_daily_performance AS
SELECT
    k.date_id,
    k.site_code,
    k.site_name,
    k.line_code,
    k.line_name,

    -- Production KPIs
    k.planned_quantity,
    k.actual_quantity,
    k.good_quantity,
    k.reject_quantity,
    k.operating_time_min,
    k.planned_production_time_min,
    k.availability,
    k.performance,
    k.quality,
    k.oee,
    k.production_attainment,
    k.good_output_attainment,

    -- Loss accounting
    l.theoretical_capacity_units,
    l.availability_loss_units,
    l.planned_downtime_loss_units,
    l.unplanned_downtime_loss_units,
    l.changeover_loss_units_subset,
    l.performance_loss_units,
    l.quality_loss_units,
    l.total_technical_loss_units,
    l.plan_shortfall_units,
    l.planned_downtime_opportunity_eur,
    l.unplanned_downtime_opportunity_eur,
    l.changeover_opportunity_eur_subset,
    l.performance_opportunity_eur,
    l.quality_opportunity_eur,
    l.total_technical_opportunity_eur,
    l.plan_shortfall_opportunity_eur,

    -- Energy
    e.electricity_kwh,
    e.avg_demand_kw,
    e.kwh_per_1000_actual_units,
    e.kwh_per_1000_good_units,
    e.kwh_per_operating_hour,
    e.kwh_per_planned_hour

FROM public.vw_line_daily_kpi k
LEFT JOIN public.vw_line_daily_loss_accounting l
    ON l.date_id = k.date_id
   AND l.site_code = k.site_code
   AND l.line_code = k.line_code
LEFT JOIN public.vw_line_daily_energy_kpi e
    ON e.date_id = k.date_id
   AND e.site_code = k.site_code
   AND e.line_code = k.line_code;


-- ============================================================
-- 3. Site-day integrated Gold model
-- Grain: one row per date_id / site
-- Expected rows: 4,386
-- Includes site auxiliary energy aggregated from shift grain.
-- ============================================================
CREATE OR REPLACE VIEW gold.vw_site_daily_performance AS
WITH aux_daily AS (
    SELECT
        to_char(timestamp_start, 'YYYYMMDD')::integer AS date_id,
        site_code,
        SUM(line_electricity_kwh) AS line_electricity_kwh,
        SUM(site_auxiliary_electricity_kwh) AS site_auxiliary_electricity_kwh,
        SUM(site_total_electricity_kwh) AS site_total_electricity_kwh,
        SUM(production_units) AS production_units,
        CASE
            WHEN SUM(site_total_electricity_kwh) = 0 THEN NULL
            ELSE SUM(site_auxiliary_electricity_kwh) / SUM(site_total_electricity_kwh)
        END AS auxiliary_energy_share,
        CASE
            WHEN SUM(production_units) = 0 THEN NULL
            ELSE SUM(site_total_electricity_kwh) / SUM(production_units) * 1000.0
        END AS total_site_kwh_per_1000_units,
        AVG(mean_air_temperature_c) AS mean_air_temperature_c
    FROM public.vw_site_auxiliary_energy_kpi
    GROUP BY
        to_char(timestamp_start, 'YYYYMMDD')::integer,
        site_code
)
SELECT
    k.date_id,
    k.site_code,
    k.site_name,

    -- Production KPIs
    k.planned_quantity,
    k.actual_quantity,
    k.good_quantity,
    k.reject_quantity,
    k.operating_time_min,
    k.planned_production_time_min,
    k.availability,
    k.performance,
    k.quality,
    k.oee,
    k.production_attainment,

    -- Loss accounting
    l.theoretical_capacity_units,
    l.availability_loss_units,
    l.planned_downtime_loss_units,
    l.unplanned_downtime_loss_units,
    l.changeover_loss_units_subset,
    l.performance_loss_units,
    l.quality_loss_units,
    l.total_technical_loss_units,
    l.plan_shortfall_units,
    l.planned_downtime_opportunity_eur,
    l.unplanned_downtime_opportunity_eur,
    l.changeover_opportunity_eur_subset,
    l.performance_opportunity_eur,
    l.quality_opportunity_eur,
    l.total_technical_opportunity_eur,
    l.plan_shortfall_opportunity_eur,

    -- Line electricity aggregation
    e.electricity_kwh,
    e.avg_line_demand_kw,
    e.kwh_per_1000_actual_units,
    e.kwh_per_1000_good_units,
    e.kwh_per_operating_hour,
    e.kwh_per_planned_hour,

    -- Site auxiliary / total energy
    a.line_electricity_kwh,
    a.site_auxiliary_electricity_kwh,
    a.site_total_electricity_kwh,
    a.auxiliary_energy_share,
    a.total_site_kwh_per_1000_units,
    a.mean_air_temperature_c

FROM public.vw_site_daily_kpi k
LEFT JOIN public.vw_site_daily_loss_accounting l
    ON l.date_id = k.date_id
   AND l.site_code = k.site_code
LEFT JOIN public.vw_site_daily_energy_kpi e
    ON e.date_id = k.date_id
   AND e.site_code = k.site_code
LEFT JOIN aux_daily a
    ON a.date_id = k.date_id
   AND a.site_code = k.site_code;


-- ============================================================
-- 4. Site executive summary
-- Grain: one row per site
-- Expected rows: 6
-- ============================================================
CREATE OR REPLACE VIEW gold.vw_site_executive_summary AS
SELECT
    p.site_code,
    p.site_name,
    p.line_count,

    -- Production benchmark/ranking
    p.avg_line_oee,
    p.min_line_oee,
    p.max_line_oee,
    p.avg_line_production_attainment,
    p.avg_line_good_output_attainment,
    p.avg_line_gross_capacity_utilization,
    p.planned_quantity,
    p.actual_quantity,
    p.good_quantity,
    p.reject_quantity,
    p.oee_rank,
    p.attainment_rank,
    p.utilization_rank,

    -- Technical and financial loss
    l.theoretical_capacity_units,
    l.planned_downtime_loss_units,
    l.unplanned_downtime_loss_units,
    l.changeover_loss_units_subset,
    l.performance_loss_units,
    l.quality_loss_units,
    l.total_technical_loss_units,
    l.planned_downtime_opportunity_eur,
    l.unplanned_downtime_opportunity_eur,
    l.changeover_opportunity_eur_subset,
    l.performance_opportunity_eur,
    l.quality_opportunity_eur,
    l.total_technical_opportunity_eur,
    l.plan_shortfall_opportunity_eur,

    -- Site energy
    a.line_electricity_kwh,
    a.site_auxiliary_electricity_kwh,
    a.site_total_electricity_kwh,
    a.production_units AS energy_production_units,
    a.auxiliary_energy_share,
    a.total_site_kwh_per_1000_units,
    a.mean_air_temperature_c,
    a.avg_auxiliary_base_kw,
    a.avg_weather_auxiliary_kw,
    a.total_site_energy_intensity_rank,
    a.auxiliary_share_rank,

    -- External benchmark electricity cost
    c.country_code,
    c.benchmark_electricity_cost_eur,
    c.benchmark_electricity_cost_eur_per_1000_units,
    c.weighted_benchmark_eur_per_kwh,
    c.cost_intensity_rank,
    c.benchmark_price_rank

FROM public.vw_site_production_rank p
LEFT JOIN public.vw_site_loss_summary l
    ON l.site_code = p.site_code
LEFT JOIN public.vw_site_auxiliary_rank a
    ON a.site_code = p.site_code
LEFT JOIN public.vw_site_electricity_cost_rank c
    ON c.site_code = p.site_code;


-- ============================================================
-- 5. DQ domain summary for reporting
-- Grain: one row per DQ domain
-- Expected rows: 7
-- ============================================================
CREATE OR REPLACE VIEW gold.vw_data_quality_domain_summary AS
SELECT
    domain_name,
    rule_count,
    passed_rules,
    failed_rules,
    evaluated_rows,
    failed_rows,
    weighted_data_quality_score,
    warning_rules
FROM public.vw_data_quality_summary;


-- ============================================================
-- 6. DQ rule detail for operational drill-down
-- Grain: one row per latest DQ rule
-- Expected rows: 29
-- ============================================================
CREATE OR REPLACE VIEW gold.vw_data_quality_rule_status AS
SELECT
    rule_code,
    rule_name,
    domain_name,
    target_object,
    rule_type,
    severity,
    run_timestamp,
    evaluated_row_count,
    failed_row_count,
    failure_rate,
    result_status,
    result_detail
FROM public.vw_data_quality_latest;
