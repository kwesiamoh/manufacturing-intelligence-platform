-- Stage 13D.2 validation
\pset pager off

\echo '=== 1. Monthly trend coverage ==='
SELECT
    MIN(month_start) AS min_month,
    MAX(month_start) AS max_month,
    COUNT(DISTINCT month_start) AS months,
    COUNT(DISTINCT site_code) AS sites,
    COUNT(DISTINCT line_code) AS lines,
    COUNT(*) AS site_line_month_rows
FROM analytics.vw_monthly_reliability_trend;

\echo ''
\echo '=== 2. Failure reconciliation ==='
SELECT
    SUM(corrective_failure_count) AS corrective_failures,
    ROUND(SUM(corrective_downtime_hours)::numeric,2)
        AS corrective_downtime_hours
FROM analytics.vw_monthly_reliability_trend;

\echo ''
\echo '=== 3. Expected reconciliation check ==='
SELECT
    CASE
        WHEN SUM(corrective_failure_count) = 46670 THEN 'PASS'
        ELSE 'CHECK'
    END AS failure_count_status,
    SUM(corrective_failure_count) AS observed_corrective_failures,
    46670 AS expected_corrective_failures
FROM analytics.vw_monthly_reliability_trend;

\echo ''
\echo '=== 4. Trend KPI sanity ==='
SELECT
    COUNT(*) FILTER (
        WHERE corrective_failures_per_1000_operating_hours < 0
    ) AS invalid_failure_rate,
    COUNT(*) FILTER (
        WHERE monthly_operating_hours_mtbf_proxy <= 0
    ) AS invalid_mtbf_proxy,
    COUNT(*) FILTER (
        WHERE mttr_hours <= 0
    ) AS invalid_mttr,
    COUNT(*) FILTER (
        WHERE corrective_downtime_to_operating_time_ratio < 0
    ) AS invalid_downtime_ratio
FROM analytics.vw_monthly_reliability_trend;

\echo ''
\echo '=== 5. Enterprise monthly reliability trend ==='
SELECT
    month_start,
    SUM(corrective_failure_count) AS corrective_failures,
    ROUND(SUM(corrective_downtime_hours)::numeric,2)
        AS corrective_downtime_h,
    ROUND(
        (
            SUM(corrective_failure_count) * 1000.0
            / NULLIF(SUM(line_operating_hours),0)
        )::numeric,
        3
    ) AS failures_per_1000_operating_h,
    ROUND(
        (
            SUM(line_operating_hours)
            / NULLIF(SUM(corrective_failure_count),0)
        )::numeric,
        2
    ) AS operating_mtbf_proxy_h,
    ROUND(
        (
            SUM(corrective_downtime_hours)
            / NULLIF(SUM(line_operating_hours),0)
        )::numeric,
        5
    ) AS downtime_to_operating_ratio
FROM analytics.vw_monthly_reliability_trend
GROUP BY month_start
ORDER BY month_start;

\echo ''
\echo '=== 6. Site trend summary ==='
SELECT
    site_code,
    SUM(corrective_failure_count) AS corrective_failures,
    ROUND(SUM(corrective_downtime_hours)::numeric,2) AS downtime_h,
    ROUND(
        (
            SUM(corrective_failure_count) * 1000.0
            / NULLIF(SUM(line_operating_hours),0)
        )::numeric,
        3
    ) AS failures_per_1000_operating_h,
    ROUND(
        (
            SUM(line_operating_hours)
            / NULLIF(SUM(corrective_failure_count),0)
        )::numeric,
        2
    ) AS operating_mtbf_proxy_h
FROM analytics.vw_monthly_reliability_trend
GROUP BY site_code
ORDER BY failures_per_1000_operating_h DESC;

\echo ''
\echo '=== 7. Equipment-type trend coverage ==='
SELECT
    MIN(month_start) AS min_month,
    MAX(month_start) AS max_month,
    COUNT(DISTINCT month_start) AS months,
    SUM(corrective_failure_count) AS corrective_failures
FROM analytics.vw_monthly_equipment_type_reliability_trend;

\echo ''
\echo '=== Stage 13D.2 validation complete ==='

\echo '=== Mandatory Stage 13D.2 gate ==='
DO $validation$
DECLARE
    bad_count bigint;
    expected_failure_events bigint;
    expected_downtime_hours numeric;
    expected_repair_hours numeric;
BEGIN
    -- Every accepted failure event must resolve to exactly one production row
    -- with the same source dataset. This protects the corrected production-date
    -- attribution from textual production-ID collisions across sources.
    SELECT COUNT(*) INTO bad_count
    FROM (
        SELECT
            f.downtime_source_dataset_id,
            f.downtime_source_record_id
        FROM analytics.vw_corrective_failure_event f
        LEFT JOIN public.fact_production p
          ON p.source_dataset_id = f.downtime_source_dataset_id
         AND p.source_record_id = f.production_record_id
        GROUP BY
            f.downtime_source_dataset_id,
            f.downtime_source_record_id
        HAVING COUNT(p.production_id) <> 1
    ) invalid_production_link;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'Stage 13D.2 found % failure events without exactly one source-qualified production parent', bad_count;
    END IF;

    SELECT
        COUNT(*),
        COALESCE(SUM(f.failure_downtime_hours), 0),
        COALESCE(SUM(f.total_repair_duration_hours), 0)
    INTO
        expected_failure_events,
        expected_downtime_hours,
        expected_repair_hours
    FROM analytics.vw_corrective_failure_event f
    JOIN public.fact_production p
      ON p.source_dataset_id = f.downtime_source_dataset_id
     AND p.source_record_id = f.production_record_id
    JOIN public.dim_time pt
      ON pt.date_id = p.date_id
    WHERE pt.calendar_date >= DATE '2024-01-01'
      AND pt.calendar_date <= DATE '2025-12-31';

    IF (SELECT MIN(month_start) FROM analytics.vw_monthly_reliability_trend) <> DATE '2024-01-01'
       OR (SELECT MAX(month_start) FROM analytics.vw_monthly_reliability_trend) <> DATE '2025-12-01'
       OR (SELECT COUNT(DISTINCT month_start) FROM analytics.vw_monthly_reliability_trend) <> 24
       OR (SELECT COUNT(DISTINCT site_code) FROM analytics.vw_monthly_reliability_trend) <> 6
       OR (SELECT COUNT(DISTINCT line_code) FROM analytics.vw_monthly_reliability_trend) <> 30
       OR (SELECT COUNT(*) FROM analytics.vw_monthly_reliability_trend) <> 720 THEN
        RAISE EXCEPTION 'Stage 13D.2 monthly trend coverage does not match 2024-01 through 2025-12';
    END IF;

    IF COALESCE((SELECT SUM(corrective_failure_count)
                 FROM analytics.vw_monthly_reliability_trend), 0)
       <> expected_failure_events
       OR COALESCE((SELECT SUM(corrective_failure_count)
                    FROM analytics.vw_monthly_equipment_type_reliability_trend), 0)
       <> expected_failure_events THEN
        RAISE EXCEPTION 'Stage 13D.2 trends do not reconcile to canonical failure-event grain';
    END IF;
    IF ABS(COALESCE((SELECT SUM(corrective_downtime_hours)
                     FROM analytics.vw_monthly_reliability_trend), 0)
           - expected_downtime_hours) > 0.000001
       OR ABS(COALESCE((SELECT SUM(corrective_downtime_hours)
                        FROM analytics.vw_monthly_equipment_type_reliability_trend), 0)
              - expected_downtime_hours) > 0.000001 THEN
        RAISE EXCEPTION 'Stage 13D.2 trends multiplied or omitted corrective downtime';
    END IF;
    IF ABS(COALESCE((SELECT SUM(mttr_hours * corrective_failure_count)
                     FROM analytics.vw_monthly_reliability_trend), 0)
           - expected_repair_hours) > 0.000001
       OR ABS(COALESCE((SELECT SUM(mttr_hours * corrective_failure_count)
                        FROM analytics.vw_monthly_equipment_type_reliability_trend), 0)
              - expected_repair_hours) > 0.000001 THEN
        RAISE EXCEPTION 'Stage 13D.2 MTTR does not reconcile to work-order repair duration at failure-event grain';
    END IF;
    IF expected_failure_events <> 46670 THEN
        RAISE EXCEPTION 'Stage 13D.2 accepted source snapshot changed from 46,670 corrective failure events';
    END IF;

    -- Exact dimensional/month reconciliation enforces Stage 13D.2 production
    -- calendar attribution and catches any future raw text-only cross-link.
    WITH expected AS (
        SELECT
            date_trunc('month', pt.calendar_date)::date AS month_start,
            s.site_code,
            l.line_code,
            COUNT(*) AS failure_count,
            SUM(f.failure_downtime_hours) AS downtime_hours
        FROM analytics.vw_corrective_failure_event f
        JOIN public.fact_production p
          ON p.source_dataset_id = f.downtime_source_dataset_id
         AND p.source_record_id = f.production_record_id
        JOIN public.dim_time pt
          ON pt.date_id = p.date_id
        JOIN public.dim_site s
          ON s.site_id = f.site_id
        JOIN public.dim_line l
          ON l.line_id = f.line_id
        WHERE pt.calendar_date >= DATE '2024-01-01'
          AND pt.calendar_date <= DATE '2025-12-31'
        GROUP BY
            date_trunc('month', pt.calendar_date)::date,
            s.site_code,
            l.line_code
    ),
    mismatch AS (
        SELECT 1
        FROM expected e
        FULL JOIN analytics.vw_monthly_reliability_trend a
          ON a.month_start = e.month_start
         AND a.site_code = e.site_code
         AND a.line_code = e.line_code
        WHERE COALESCE(a.corrective_failure_count, 0)
              <> COALESCE(e.failure_count, 0)
           OR ABS(COALESCE(a.corrective_downtime_hours, 0)
                  - COALESCE(e.downtime_hours, 0)) > 0.000001
    )
    SELECT COUNT(*) INTO bad_count FROM mismatch;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'Stage 13D.2 found % site-line-month attribution mismatches', bad_count;
    END IF;

    SELECT COUNT(*) INTO bad_count
    FROM analytics.vw_monthly_reliability_trend
    WHERE corrective_failures_per_1000_operating_hours < 0
       OR monthly_operating_hours_mtbf_proxy <= 0
       OR mttr_hours <= 0
       OR corrective_downtime_to_operating_time_ratio < 0;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'Stage 13D.2 KPI sanity gate found % invalid monthly rows', bad_count;
    END IF;
END
$validation$;
