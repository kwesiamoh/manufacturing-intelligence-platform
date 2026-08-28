\pset pager off

\echo '=== Stage 6A row counts ==='
SELECT 'vw_shift_energy_kpi' AS object_name, COUNT(*) AS row_count
FROM vw_shift_energy_kpi
UNION ALL
SELECT 'vw_line_daily_energy_kpi', COUNT(*)
FROM vw_line_daily_energy_kpi
UNION ALL
SELECT 'vw_site_daily_energy_kpi', COUNT(*)
FROM vw_site_daily_energy_kpi
UNION ALL
SELECT 'vw_line_energy_summary', COUNT(*)
FROM vw_line_energy_summary
UNION ALL
SELECT 'vw_line_energy_rank', COUNT(*)
FROM vw_line_energy_rank
UNION ALL
SELECT 'vw_site_energy_summary', COUNT(*)
FROM vw_site_energy_summary
UNION ALL
SELECT 'vw_site_energy_rank', COUNT(*)
FROM vw_site_energy_rank;

\echo '=== Energy lineage completeness: expected zero ==='
SELECT COUNT(*) AS bad_rows
FROM vw_shift_energy_kpi
WHERE production_record_id IS NULL
   OR site_code IS NULL
   OR line_code IS NULL
   OR product_code IS NULL;

\echo '=== Positive energy/intensity checks: expected all zero ==='
SELECT
    COUNT(*) FILTER (WHERE electricity_kwh <= 0) AS bad_energy,
    COUNT(*) FILTER (WHERE avg_demand_kw <= 0) AS bad_demand,
    COUNT(*) FILTER (WHERE kwh_per_1000_actual_units <= 0) AS bad_actual_intensity,
    COUNT(*) FILTER (WHERE kwh_per_1000_good_units <= 0) AS bad_good_intensity,
    COUNT(*) FILTER (WHERE kwh_per_operating_hour <= 0) AS bad_operating_hour_intensity,
    COUNT(*) FILTER (WHERE kwh_per_planned_hour <= 0) AS bad_planned_hour_intensity
FROM vw_shift_energy_kpi;

\echo '=== Shift energy -> line daily reconciliation: expected zero ==='
WITH shift_sum AS (
    SELECT SUM(electricity_kwh) AS energy
    FROM vw_shift_energy_kpi
),
daily_sum AS (
    SELECT SUM(electricity_kwh) AS energy
    FROM vw_line_daily_energy_kpi
)
SELECT
    CASE
        WHEN ABS(s.energy - d.energy) <= 0.001 THEN 0
        ELSE 1
    END AS bad_reconciliation
FROM shift_sum s, daily_sum d;

\echo '=== Line summary -> site summary reconciliation: expected zero ==='
WITH line_sum AS (
    SELECT SUM(electricity_kwh) AS energy
    FROM vw_line_energy_summary
),
site_sum AS (
    SELECT SUM(electricity_kwh) AS energy
    FROM vw_site_energy_summary
)
SELECT
    CASE
        WHEN ABS(l.energy - s.energy) <= 0.001 THEN 0
        ELSE 1
    END AS bad_reconciliation
FROM line_sum l, site_sum s;

\echo '=== Site line counts: expected five each ==='
SELECT
    site_code,
    line_count
FROM vw_site_energy_summary
ORDER BY site_code;

\echo '=== Site energy-intensity ranking ==='
SELECT
    site_code,
    ROUND(electricity_kwh::numeric, 0) AS electricity_kwh,
    ROUND(kwh_per_1000_good_units::numeric, 4) AS kwh_per_1000_good_units,
    energy_intensity_rank
FROM vw_site_energy_rank
ORDER BY energy_intensity_rank, site_code;

\echo '=== Best and worst lines by energy intensity ==='
(
    SELECT
        'BEST' AS group_name,
        enterprise_energy_intensity_rank AS rank,
        site_code,
        line_code,
        ROUND(kwh_per_1000_good_units::numeric, 4) AS kwh_per_1000_good_units
    FROM vw_line_energy_rank
    ORDER BY enterprise_energy_intensity_rank
    LIMIT 5
)
UNION ALL
(
    SELECT
        'WORST' AS group_name,
        enterprise_energy_intensity_rank AS rank,
        site_code,
        line_code,
        ROUND(kwh_per_1000_good_units::numeric, 4) AS kwh_per_1000_good_units
    FROM vw_line_energy_rank
    ORDER BY enterprise_energy_intensity_rank DESC
    LIMIT 5
)
ORDER BY group_name, rank;

\echo '=== Mandatory Stage 6A gate ==='
DO $validation$
DECLARE
    bad_count bigint;
    shift_energy numeric;
    daily_energy numeric;
    line_energy numeric;
    site_energy numeric;
BEGIN
    IF (SELECT COUNT(*) FROM vw_shift_energy_kpi) <> 65790
       OR (SELECT COUNT(*) FROM vw_line_daily_energy_kpi) <> 21930
       OR (SELECT COUNT(*) FROM vw_site_daily_energy_kpi) <> 4386
       OR (SELECT COUNT(*) FROM vw_line_energy_summary) <> 30
       OR (SELECT COUNT(*) FROM vw_line_energy_rank) <> 30
       OR (SELECT COUNT(*) FROM vw_site_energy_summary) <> 6
       OR (SELECT COUNT(*) FROM vw_site_energy_rank) <> 6 THEN
        RAISE EXCEPTION 'Stage 6A view row counts do not match the canonical population';
    END IF;

    SELECT COUNT(*) INTO bad_count
    FROM vw_shift_energy_kpi
    WHERE production_record_id IS NULL OR site_code IS NULL OR line_code IS NULL
       OR product_code IS NULL OR electricity_kwh <= 0 OR avg_demand_kw <= 0
       OR kwh_per_1000_actual_units <= 0 OR kwh_per_1000_good_units <= 0
       OR kwh_per_operating_hour <= 0 OR kwh_per_planned_hour <= 0;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'Stage 6A energy gate found % invalid shift rows', bad_count;
    END IF;

    SELECT SUM(electricity_kwh) INTO shift_energy FROM vw_shift_energy_kpi;
    SELECT SUM(electricity_kwh) INTO daily_energy FROM vw_line_daily_energy_kpi;
    SELECT SUM(electricity_kwh) INTO line_energy FROM vw_line_energy_summary;
    SELECT SUM(electricity_kwh) INTO site_energy FROM vw_site_energy_summary;
    IF ABS(shift_energy - daily_energy) > 0.001
       OR ABS(line_energy - site_energy) > 0.001 THEN
        RAISE EXCEPTION 'Stage 6A energy aggregation reconciliation failed';
    END IF;

    IF EXISTS (SELECT 1 FROM vw_site_energy_summary WHERE line_count <> 5) THEN
        RAISE EXCEPTION 'Stage 6A site energy summary does not contain five lines per site';
    END IF;
END
$validation$;
