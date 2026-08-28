-- production loss corrected — Exact technical-capacity loss accounting and financial translation.

CREATE OR REPLACE VIEW vw_shift_loss_accounting AS
WITH base AS (
    SELECT
        l.*,
        (l.planned_production_time_min / 60.0) * l.nominal_rate
            AS theoretical_capacity_units,
        (l.operating_time_min / 60.0) * l.nominal_rate
            AS operating_capacity_units
    FROM vw_shift_production_loss l
),
classified AS (
    SELECT
        b.*,

        GREATEST(
            b.theoretical_capacity_units - b.operating_capacity_units,
            0
        ) AS availability_loss_units_exact,

        b.planned_downtime_min * b.nominal_rate / 60.0
            AS planned_downtime_loss_units_exact,

        b.unplanned_downtime_min * b.nominal_rate / 60.0
            AS unplanned_downtime_loss_units_exact,

        b.changeover_downtime_min * b.nominal_rate / 60.0
            AS changeover_loss_units_subset,

        GREATEST(
            b.operating_capacity_units - b.actual_quantity,
            0
        ) AS performance_loss_units_exact,

        b.reject_quantity::numeric
            AS quality_loss_units_exact,

        GREATEST(
            b.planned_quantity - b.good_quantity,
            0
        )::numeric AS plan_shortfall_units
    FROM base b
)
SELECT
    c.*,

    c.availability_loss_units_exact
      + c.performance_loss_units_exact
      + c.quality_loss_units_exact
        AS total_technical_loss_units,

    GREATEST(
        c.theoretical_capacity_units - c.good_quantity,
        0
    ) AS technical_capacity_gap_units,

    CASE
        WHEN c.theoretical_capacity_units > 0
        THEN c.good_quantity::numeric / c.theoretical_capacity_units
    END AS technical_output_efficiency,

    v.standard_loss_value_eur_per_unit,
    v.value_basis,
    v.assumption_class,

    c.planned_downtime_loss_units_exact
      * v.standard_loss_value_eur_per_unit
        AS planned_downtime_opportunity_eur,

    c.unplanned_downtime_loss_units_exact
      * v.standard_loss_value_eur_per_unit
        AS unplanned_downtime_opportunity_eur,

    c.changeover_loss_units_subset
      * v.standard_loss_value_eur_per_unit
        AS changeover_opportunity_eur_subset,

    c.performance_loss_units_exact
      * v.standard_loss_value_eur_per_unit
        AS performance_opportunity_eur,

    c.quality_loss_units_exact
      * v.standard_loss_value_eur_per_unit
        AS quality_opportunity_eur,

    (
        c.availability_loss_units_exact
        + c.performance_loss_units_exact
        + c.quality_loss_units_exact
    ) * v.standard_loss_value_eur_per_unit
        AS total_technical_opportunity_eur,

    c.plan_shortfall_units
      * v.standard_loss_value_eur_per_unit
        AS plan_shortfall_opportunity_eur

FROM classified c
LEFT JOIN cfg_product_loss_value v
  ON v.product_code = c.product_code;


CREATE OR REPLACE VIEW vw_line_daily_loss_accounting AS
SELECT
    date_id,
    site_code,
    site_name,
    line_code,
    line_name,

    SUM(theoretical_capacity_units) AS theoretical_capacity_units,
    SUM(good_quantity) AS good_quantity,
    SUM(availability_loss_units_exact) AS availability_loss_units,
    SUM(planned_downtime_loss_units_exact) AS planned_downtime_loss_units,
    SUM(unplanned_downtime_loss_units_exact) AS unplanned_downtime_loss_units,
    SUM(changeover_loss_units_subset) AS changeover_loss_units_subset,
    SUM(performance_loss_units_exact) AS performance_loss_units,
    SUM(quality_loss_units_exact) AS quality_loss_units,
    SUM(total_technical_loss_units) AS total_technical_loss_units,
    SUM(plan_shortfall_units) AS plan_shortfall_units,

    SUM(planned_downtime_opportunity_eur) AS planned_downtime_opportunity_eur,
    SUM(unplanned_downtime_opportunity_eur) AS unplanned_downtime_opportunity_eur,
    SUM(changeover_opportunity_eur_subset) AS changeover_opportunity_eur_subset,
    SUM(performance_opportunity_eur) AS performance_opportunity_eur,
    SUM(quality_opportunity_eur) AS quality_opportunity_eur,
    SUM(total_technical_opportunity_eur) AS total_technical_opportunity_eur,
    SUM(plan_shortfall_opportunity_eur) AS plan_shortfall_opportunity_eur

FROM vw_shift_loss_accounting
GROUP BY
    date_id,
    site_code,
    site_name,
    line_code,
    line_name;


CREATE OR REPLACE VIEW vw_site_daily_loss_accounting AS
SELECT
    date_id,
    site_code,
    site_name,

    SUM(theoretical_capacity_units) AS theoretical_capacity_units,
    SUM(good_quantity) AS good_quantity,
    SUM(availability_loss_units_exact) AS availability_loss_units,
    SUM(planned_downtime_loss_units_exact) AS planned_downtime_loss_units,
    SUM(unplanned_downtime_loss_units_exact) AS unplanned_downtime_loss_units,
    SUM(changeover_loss_units_subset) AS changeover_loss_units_subset,
    SUM(performance_loss_units_exact) AS performance_loss_units,
    SUM(quality_loss_units_exact) AS quality_loss_units,
    SUM(total_technical_loss_units) AS total_technical_loss_units,
    SUM(plan_shortfall_units) AS plan_shortfall_units,

    SUM(planned_downtime_opportunity_eur) AS planned_downtime_opportunity_eur,
    SUM(unplanned_downtime_opportunity_eur) AS unplanned_downtime_opportunity_eur,
    SUM(changeover_opportunity_eur_subset) AS changeover_opportunity_eur_subset,
    SUM(performance_opportunity_eur) AS performance_opportunity_eur,
    SUM(quality_opportunity_eur) AS quality_opportunity_eur,
    SUM(total_technical_opportunity_eur) AS total_technical_opportunity_eur,
    SUM(plan_shortfall_opportunity_eur) AS plan_shortfall_opportunity_eur

FROM vw_shift_loss_accounting
GROUP BY
    date_id,
    site_code,
    site_name;


CREATE OR REPLACE VIEW vw_site_loss_summary AS
SELECT
    site_code,
    site_name,

    SUM(theoretical_capacity_units) AS theoretical_capacity_units,
    SUM(good_quantity) AS good_quantity,

    SUM(planned_downtime_loss_units_exact) AS planned_downtime_loss_units,
    SUM(unplanned_downtime_loss_units_exact) AS unplanned_downtime_loss_units,
    SUM(changeover_loss_units_subset) AS changeover_loss_units_subset,
    SUM(performance_loss_units_exact) AS performance_loss_units,
    SUM(quality_loss_units_exact) AS quality_loss_units,
    SUM(total_technical_loss_units) AS total_technical_loss_units,

    SUM(planned_downtime_opportunity_eur) AS planned_downtime_opportunity_eur,
    SUM(unplanned_downtime_opportunity_eur) AS unplanned_downtime_opportunity_eur,
    SUM(changeover_opportunity_eur_subset) AS changeover_opportunity_eur_subset,
    SUM(performance_opportunity_eur) AS performance_opportunity_eur,
    SUM(quality_opportunity_eur) AS quality_opportunity_eur,
    SUM(total_technical_opportunity_eur) AS total_technical_opportunity_eur,
    SUM(plan_shortfall_opportunity_eur) AS plan_shortfall_opportunity_eur

FROM vw_shift_loss_accounting
GROUP BY site_code, site_name;
