\pset pager off

\echo '=== Stage 5C row counts ==='
SELECT 'vw_line_performance_summary' AS object_name, COUNT(*) AS row_count
FROM vw_line_performance_summary
UNION ALL
SELECT 'vw_line_performance_rank', COUNT(*)
FROM vw_line_performance_rank
UNION ALL
SELECT 'vw_downtime_reason_pareto', COUNT(*)
FROM vw_downtime_reason_pareto
UNION ALL
SELECT 'vw_changeover_summary', COUNT(*)
FROM vw_changeover_summary
UNION ALL
SELECT 'vw_site_production_benchmark', COUNT(*)
FROM vw_site_production_benchmark
UNION ALL
SELECT 'vw_site_production_rank', COUNT(*)
FROM vw_site_production_rank;

\echo '=== Line KPI bounds: expected all zero ==='
SELECT
    COUNT(*) FILTER (WHERE availability < 0 OR availability > 1.000001) AS bad_availability,
    COUNT(*) FILTER (WHERE performance < 0 OR performance > 1.000001) AS bad_performance,
    COUNT(*) FILTER (WHERE quality < 0 OR quality > 1.000001) AS bad_quality,
    COUNT(*) FILTER (WHERE oee < 0 OR oee > 1.000001) AS bad_oee,
    COUNT(*) FILTER (WHERE gross_capacity_utilization < 0 OR gross_capacity_utilization > 1.000001) AS bad_utilization
FROM vw_line_performance_summary;

\echo '=== Line OEE identity: expected zero ==='
SELECT COUNT(*) AS bad_rows
FROM vw_line_performance_summary
WHERE ABS(oee - availability * performance * quality) > 0.0000001;

\echo '=== Downtime Pareto share reconciliation: expected six sites near 1.0 ==='
SELECT
    site_code,
    ROUND(SUM(downtime_share)::numeric, 6) AS downtime_share_sum
FROM vw_downtime_reason_pareto
GROUP BY site_code
ORDER BY site_code;

\echo '=== Pareto cumulative end-point check: expected zero ==='
WITH x AS (
    SELECT
        site_code,
        MAX(cumulative_downtime_share) AS max_cumulative_share
    FROM vw_downtime_reason_pareto
    GROUP BY site_code
)
SELECT COUNT(*) AS bad_sites
FROM x
WHERE ABS(max_cumulative_share - 1.0) > 0.000001;

\echo '=== Changeover sanity: expected zero ==='
SELECT COUNT(*) AS bad_rows
FROM vw_changeover_summary
WHERE changeover_event_count <= 0
   OR total_changeover_min <= 0
   OR avg_changeover_min <= 0
   OR median_changeover_min <= 0
   OR min_changeover_min <= 0
   OR max_changeover_min <= 0;

\echo '=== Site benchmark line count: expected five each ==='
SELECT
    site_code,
    line_count
FROM vw_site_production_benchmark
ORDER BY site_code;

\echo '=== Site ranking summary ==='
SELECT
    site_code,
    ROUND(avg_line_oee::numeric, 4) AS avg_line_oee,
    ROUND(avg_line_production_attainment::numeric, 4) AS avg_attainment,
    ROUND(avg_line_gross_capacity_utilization::numeric, 4) AS avg_utilization,
    oee_rank,
    attainment_rank,
    utilization_rank
FROM vw_site_production_rank
ORDER BY oee_rank, site_code;

\echo '=== Top 10 downtime reasons by site / Pareto rank ==='
SELECT
    site_code,
    pareto_rank,
    failure_category,
    failure_reason,
    planned_flag,
    event_count,
    ROUND(downtime_min::numeric, 2) AS downtime_min,
    ROUND((downtime_share * 100)::numeric, 2) AS downtime_pct,
    ROUND((cumulative_downtime_share * 100)::numeric, 2) AS cumulative_pct
FROM vw_downtime_reason_pareto
WHERE pareto_rank <= 10
ORDER BY site_code, pareto_rank;

\echo '=== Mandatory Stage 5C gate ==='
DO $validation$
DECLARE
    bad_count bigint;
BEGIN
    IF (SELECT COUNT(*) FROM vw_line_performance_summary) <> 30
       OR (SELECT COUNT(*) FROM vw_line_performance_rank) <> 30
       OR (SELECT COUNT(*) FROM vw_site_production_benchmark) <> 6
       OR (SELECT COUNT(*) FROM vw_site_production_rank) <> 6
       OR NOT EXISTS (SELECT 1 FROM vw_downtime_reason_pareto)
       OR NOT EXISTS (SELECT 1 FROM vw_changeover_summary) THEN
        RAISE EXCEPTION 'Stage 5C benchmark views have incomplete canonical coverage';
    END IF;

    SELECT COUNT(*) INTO bad_count
    FROM vw_line_performance_summary
    WHERE availability < 0 OR availability > 1.000001
       OR performance < 0 OR performance > 1.000001
       OR quality < 0 OR quality > 1.000001
       OR oee < 0 OR oee > 1.000001
       OR gross_capacity_utilization < 0 OR gross_capacity_utilization > 1.000001
       OR ABS(oee - availability * performance * quality) > 0.0000001;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'Stage 5C KPI gate found % invalid line rows', bad_count;
    END IF;

    SELECT COUNT(*) INTO bad_count
    FROM (
        SELECT site_code
        FROM vw_downtime_reason_pareto
        GROUP BY site_code
        HAVING ABS(SUM(downtime_share) - 1.0) > 0.000001
            OR ABS(MAX(cumulative_downtime_share) - 1.0) > 0.000001
    ) x;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'Stage 5C Pareto gate found % sites that do not reconcile to 1.0', bad_count;
    END IF;

    SELECT COUNT(*) INTO bad_count
    FROM vw_changeover_summary
    WHERE changeover_event_count <= 0 OR total_changeover_min <= 0
       OR avg_changeover_min <= 0 OR median_changeover_min <= 0
       OR min_changeover_min <= 0 OR max_changeover_min <= 0;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'Stage 5C changeover gate found % invalid rows', bad_count;
    END IF;

    IF EXISTS (SELECT 1 FROM vw_site_production_benchmark WHERE line_count <> 5) THEN
        RAISE EXCEPTION 'Stage 5C site benchmark does not contain five lines per site';
    END IF;
END
$validation$;
