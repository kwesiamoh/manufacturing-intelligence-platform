\pset pager off

\echo '=== production loss config validation ==='
SELECT
    COUNT(*) AS product_value_rows,
    COUNT(*) FILTER (WHERE standard_loss_value_eur_per_unit IS NULL) AS null_values,
    COUNT(*) FILTER (WHERE standard_loss_value_eur_per_unit < 0) AS negative_values
FROM cfg_product_loss_value;

\echo '=== production loss row counts ==='
SELECT 'vw_shift_loss_accounting' AS object_name, COUNT(*) AS row_count
FROM vw_shift_loss_accounting
UNION ALL
SELECT 'vw_line_daily_loss_accounting', COUNT(*)
FROM vw_line_daily_loss_accounting
UNION ALL
SELECT 'vw_site_daily_loss_accounting', COUNT(*)
FROM vw_site_daily_loss_accounting
UNION ALL
SELECT 'vw_site_loss_summary', COUNT(*)
FROM vw_site_loss_summary;

\echo '=== Missing product valuations: expected zero ==='
SELECT COUNT(*) AS bad_rows
FROM vw_shift_loss_accounting
WHERE standard_loss_value_eur_per_unit IS NULL;

\echo '=== Exact technical loss bridge: expected zero ==='
SELECT COUNT(*) AS bad_rows
FROM vw_shift_loss_accounting
WHERE ABS(
    technical_capacity_gap_units
    - (
        availability_loss_units_exact
        + performance_loss_units_exact
        + quality_loss_units_exact
      )
) > 0.001;

\echo '=== Availability split reconciliation: expected zero ==='
SELECT COUNT(*) AS bad_rows
FROM vw_shift_loss_accounting
WHERE ABS(
    availability_loss_units_exact
    - (
        planned_downtime_loss_units_exact
        + unplanned_downtime_loss_units_exact
      )
) > 0.001;

\echo '=== Changeover subset check: expected zero ==='
SELECT COUNT(*) AS bad_rows
FROM vw_shift_loss_accounting
WHERE changeover_loss_units_subset - planned_downtime_loss_units_exact > 0.001;

\echo '=== OEE / technical output efficiency identity: expected zero ==='
SELECT COUNT(*) AS bad_rows
FROM vw_shift_loss_accounting
WHERE ABS(oee - technical_output_efficiency) > 0.0000001;

\echo '=== EUR bridge: expected zero ==='
SELECT COUNT(*) AS bad_rows
FROM vw_shift_loss_accounting
WHERE ABS(
    total_technical_opportunity_eur
    - (
        planned_downtime_opportunity_eur
        + unplanned_downtime_opportunity_eur
        + performance_opportunity_eur
        + quality_opportunity_eur
      )
) > 0.01;

\echo '=== Non-negative loss check: expected all zero ==='
SELECT
    COUNT(*) FILTER (WHERE availability_loss_units_exact < 0) AS bad_availability,
    COUNT(*) FILTER (WHERE performance_loss_units_exact < 0) AS bad_performance,
    COUNT(*) FILTER (WHERE quality_loss_units_exact < 0) AS bad_quality,
    COUNT(*) FILTER (WHERE total_technical_loss_units < 0) AS bad_total,
    COUNT(*) FILTER (WHERE total_technical_opportunity_eur < 0) AS bad_eur
FROM vw_shift_loss_accounting;

\echo '=== Site loss summary ==='
SELECT
    site_code,
    ROUND(total_technical_loss_units::numeric, 0) AS technical_loss_units,
    ROUND(total_technical_opportunity_eur::numeric, 2) AS technical_opportunity_eur,
    ROUND(plan_shortfall_opportunity_eur::numeric, 2) AS plan_shortfall_opportunity_eur
FROM vw_site_loss_summary
ORDER BY total_technical_opportunity_eur DESC;

\echo '=== Mandatory production loss gate ==='
DO $validation$
DECLARE
    bad_count bigint;
BEGIN
    IF (SELECT COUNT(*) FROM cfg_product_loss_value) <> 6
       OR EXISTS (
            SELECT 1 FROM cfg_product_loss_value
            WHERE standard_loss_value_eur_per_unit IS NULL
               OR standard_loss_value_eur_per_unit < 0
       ) THEN
        RAISE EXCEPTION 'production loss product loss-value configuration is incomplete or invalid';
    END IF;

    IF (SELECT COUNT(*) FROM vw_shift_loss_accounting) <> 65790
       OR (SELECT COUNT(*) FROM vw_line_daily_loss_accounting) <> 21930
       OR (SELECT COUNT(*) FROM vw_site_daily_loss_accounting) <> 4386
       OR (SELECT COUNT(*) FROM vw_site_loss_summary) <> 6 THEN
        RAISE EXCEPTION 'production loss view row counts do not match the canonical population';
    END IF;

    SELECT COUNT(*) INTO bad_count
    FROM vw_shift_loss_accounting
    WHERE standard_loss_value_eur_per_unit IS NULL
       OR ABS(technical_capacity_gap_units
              - availability_loss_units_exact
              - performance_loss_units_exact
              - quality_loss_units_exact) > 0.001
       OR ABS(availability_loss_units_exact
              - planned_downtime_loss_units_exact
              - unplanned_downtime_loss_units_exact) > 0.001
       OR changeover_loss_units_subset - planned_downtime_loss_units_exact > 0.001
       OR ABS(oee - technical_output_efficiency) > 0.0000001
       OR ABS(total_technical_opportunity_eur
              - planned_downtime_opportunity_eur
              - unplanned_downtime_opportunity_eur
              - performance_opportunity_eur
              - quality_opportunity_eur) > 0.01
       OR availability_loss_units_exact < 0
       OR performance_loss_units_exact < 0
       OR quality_loss_units_exact < 0
       OR total_technical_loss_units < 0
       OR total_technical_opportunity_eur < 0;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'production loss accounting gate found % invalid shift rows', bad_count;
    END IF;
END
$validation$;
