\pset pager off

\echo '=== OEE row counts ==='
SELECT 'vw_shift_production_kpi' AS object_name, COUNT(*) AS row_count FROM vw_shift_production_kpi
UNION ALL SELECT 'vw_shift_production_loss', COUNT(*) FROM vw_shift_production_loss
UNION ALL SELECT 'vw_line_daily_kpi', COUNT(*) FROM vw_line_daily_kpi
UNION ALL SELECT 'vw_site_daily_kpi', COUNT(*) FROM vw_site_daily_kpi;

\echo '=== OEE component bounds ==='
SELECT
    COUNT(*) FILTER (WHERE availability < 0 OR availability > 1.000001) AS bad_availability,
    COUNT(*) FILTER (WHERE performance < 0 OR performance > 1.000001) AS bad_performance,
    COUNT(*) FILTER (WHERE quality < 0 OR quality > 1.000001) AS bad_quality,
    COUNT(*) FILTER (WHERE oee < 0 OR oee > 1.000001) AS bad_oee
FROM vw_shift_production_kpi;

\echo '=== OEE identity check ==='
SELECT COUNT(*) AS bad_rows
FROM vw_shift_production_kpi
WHERE ABS(oee - (availability * performance * quality)) > 0.0000001;

\echo '=== Quantity reconciliation ==='
SELECT COUNT(*) AS bad_rows
FROM vw_shift_production_kpi
WHERE actual_quantity <> good_quantity + reject_quantity;

\echo '=== Downtime reconciliation ==='
SELECT COUNT(*) AS bad_rows
FROM vw_shift_production_loss
WHERE ABS(
    planned_production_time_min
    - operating_time_min
    - planned_downtime_min
    - unplanned_downtime_min
) > 0.001;

\echo '=== Loss non-negativity ==='
SELECT
    COUNT(*) FILTER (WHERE planned_downtime_loss_units < 0) AS bad_planned_loss,
    COUNT(*) FILTER (WHERE unplanned_downtime_loss_units < 0) AS bad_unplanned_loss,
    COUNT(*) FILTER (WHERE changeover_loss_units < 0) AS bad_changeover_loss,
    COUNT(*) FILTER (WHERE speed_loss_units < 0) AS bad_speed_loss,
    COUNT(*) FILTER (WHERE quality_loss_units < 0) AS bad_quality_loss
FROM vw_shift_production_loss;

\echo '=== Example site summary ==='
SELECT
    site_code,
    ROUND(AVG(availability)::numeric, 4) AS avg_availability,
    ROUND(AVG(performance)::numeric, 4) AS avg_performance,
    ROUND(AVG(quality)::numeric, 4) AS avg_quality,
    ROUND(AVG(oee)::numeric, 4) AS avg_oee,
    ROUND(AVG(production_attainment)::numeric, 4) AS avg_attainment
FROM vw_shift_production_kpi
GROUP BY site_code
ORDER BY site_code;

\echo '=== Mandatory OEE gate ==='
DO $validation$
DECLARE
    bad_count bigint;
BEGIN
    IF (SELECT COUNT(*) FROM vw_shift_production_kpi) <> 65790
       OR (SELECT COUNT(*) FROM vw_shift_production_loss) <> 65790
       OR (SELECT COUNT(*) FROM vw_line_daily_kpi) <> 21930
       OR (SELECT COUNT(*) FROM vw_site_daily_kpi) <> 4386 THEN
        RAISE EXCEPTION 'OEE view row counts do not match the canonical population';
    END IF;

    SELECT COUNT(*) INTO bad_count
    FROM vw_shift_production_kpi
    WHERE availability < 0 OR availability > 1.000001
       OR performance < 0 OR performance > 1.000001
       OR quality < 0 OR quality > 1.000001
       OR oee < 0 OR oee > 1.000001
       OR ABS(oee - (availability * performance * quality)) > 0.0000001
       OR actual_quantity <> good_quantity + reject_quantity;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'OEE KPI gate found % invalid shift rows', bad_count;
    END IF;

    SELECT COUNT(*) INTO bad_count
    FROM vw_shift_production_loss
    WHERE ABS(planned_production_time_min - operating_time_min
              - planned_downtime_min - unplanned_downtime_min) > 0.001
       OR planned_downtime_loss_units < 0
       OR unplanned_downtime_loss_units < 0
       OR changeover_loss_units < 0
       OR speed_loss_units < 0
       OR quality_loss_units < 0;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'OEE loss gate found % invalid shift rows', bad_count;
    END IF;
END
$validation$;
