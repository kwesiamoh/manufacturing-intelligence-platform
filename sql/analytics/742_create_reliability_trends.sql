-- reliability-trend / 16A.6: Corrected Reliability Trends
-- Monthly attribution uses the linked production shift date rather than the
-- raw downtime timestamp so overnight events align with their operating period.
-- Failure counts and downtime are sourced from one row per source-qualified
-- downtime event; work-order repair durations are aggregated at that grain.
-- Source: SYNTHETIC_ENTERPRISE integration layer.

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.vw_monthly_reliability_trend AS
WITH linked_failure AS (
    SELECT
        date_trunc('month', pt.calendar_date)::date AS month_start,
        f.site_id,
        f.line_id,
        f.equipment_id,
        f.total_repair_duration_hours AS repair_duration_hours,
        f.failure_downtime_hours AS downtime_hours
    FROM analytics.vw_corrective_failure_event f
    JOIN public.dim_equipment e
      ON e.equipment_id = f.equipment_id
    JOIN public.fact_production p
      ON p.source_dataset_id = f.downtime_source_dataset_id
     AND p.source_record_id = f.production_record_id
    JOIN public.dim_time pt
      ON pt.date_id = p.date_id
    WHERE pt.calendar_date >= DATE '2024-01-01'
      AND pt.calendar_date <= DATE '2025-12-31'
),
failure_monthly AS (
    SELECT
        month_start,
        site_id,
        line_id,
        COUNT(*) AS corrective_failure_count,
        SUM(downtime_hours) AS corrective_downtime_hours,
        AVG(repair_duration_hours) AS mttr_hours,
        COUNT(DISTINCT equipment_id) AS affected_equipment_count
    FROM linked_failure
    GROUP BY month_start, site_id, line_id
),
operating_monthly AS (
    SELECT
        date_trunc('month', t.calendar_date)::date AS month_start,
        p.site_id,
        p.line_id,
        SUM(p.operating_time_min) / 60.0 AS line_operating_hours,
        SUM(p.planned_production_time_min) / 60.0 AS planned_production_hours
    FROM public.fact_production p
    JOIN public.dim_time t
      ON t.date_id = p.date_id
    WHERE t.calendar_date >= DATE '2024-01-01'
      AND t.calendar_date <= DATE '2025-12-31'
    GROUP BY
        date_trunc('month', t.calendar_date)::date,
        p.site_id,
        p.line_id
)
SELECT
    o.month_start,
    s.site_code,
    s.site_name,
    l.line_code,
    l.line_name,
    COALESCE(f.corrective_failure_count, 0) AS corrective_failure_count,
    COALESCE(f.corrective_downtime_hours, 0) AS corrective_downtime_hours,
    f.mttr_hours,
    COALESCE(f.affected_equipment_count, 0) AS affected_equipment_count,
    o.line_operating_hours,
    o.planned_production_hours,
    CASE
        WHEN o.line_operating_hours > 0
        THEN COALESCE(f.corrective_failure_count, 0) * 1000.0
             / o.line_operating_hours
    END AS corrective_failures_per_1000_operating_hours,
    CASE
        WHEN COALESCE(f.corrective_failure_count, 0) > 0
        THEN o.line_operating_hours / f.corrective_failure_count
    END AS monthly_operating_hours_mtbf_proxy,
    CASE
        WHEN o.line_operating_hours > 0
        THEN COALESCE(f.corrective_downtime_hours, 0)
             / o.line_operating_hours
    END AS corrective_downtime_to_operating_time_ratio
FROM operating_monthly o
LEFT JOIN failure_monthly f
  ON f.month_start = o.month_start
 AND f.site_id = o.site_id
 AND f.line_id = o.line_id
JOIN public.dim_site s
  ON s.site_id = o.site_id
JOIN public.dim_line l
  ON l.line_id = o.line_id;

CREATE OR REPLACE VIEW analytics.vw_monthly_equipment_type_reliability_trend AS
WITH linked_failure AS (
    SELECT
        date_trunc('month', pt.calendar_date)::date AS month_start,
        f.site_id,
        e.equipment_type,
        e.equipment_id,
        f.total_repair_duration_hours AS repair_duration_hours,
        f.failure_downtime_hours AS downtime_hours
    FROM analytics.vw_corrective_failure_event f
    JOIN public.dim_equipment e
      ON e.equipment_id = f.equipment_id
    JOIN public.fact_production p
      ON p.source_dataset_id = f.downtime_source_dataset_id
     AND p.source_record_id = f.production_record_id
    JOIN public.dim_time pt
      ON pt.date_id = p.date_id
    WHERE pt.calendar_date >= DATE '2024-01-01'
      AND pt.calendar_date <= DATE '2025-12-31'
)
SELECT
    lf.month_start,
    s.site_code,
    s.site_name,
    lf.equipment_type,
    COUNT(*) AS corrective_failure_count,
    COUNT(DISTINCT lf.equipment_id) AS affected_equipment_count,
    SUM(lf.downtime_hours) AS corrective_downtime_hours,
    AVG(lf.repair_duration_hours) AS mttr_hours,
    AVG(lf.downtime_hours) AS avg_corrective_downtime_per_failure_hours
FROM linked_failure lf
JOIN public.dim_site s
  ON s.site_id = lf.site_id
GROUP BY
    lf.month_start,
    s.site_code,
    s.site_name,
    lf.equipment_type;
