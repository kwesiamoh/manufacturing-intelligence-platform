-- Stage 13D: Reliability Trends
-- Source: SYNTHETIC_ENTERPRISE integration layer.
-- No maintenance-cost or production-loss metrics are used because those fields
-- are not populated in the current corrective-failure event population.

CREATE SCHEMA IF NOT EXISTS analytics;

DROP VIEW IF EXISTS analytics.vw_monthly_reliability_trend;
DROP VIEW IF EXISTS analytics.vw_monthly_equipment_type_reliability_trend;

CREATE VIEW analytics.vw_monthly_reliability_trend AS
WITH linked_failure AS (
    SELECT
        date_trunc('month', d.event_start)::date AS month_start,
        d.site_id,
        e.line_id,
        d.equipment_id,
        m.maintenance_id,
        m.duration_hours AS repair_duration_hours,
        d.duration_min / 60.0 AS downtime_hours
    FROM public.fact_maintenance m
    JOIN public.fact_downtime d
      ON m.downtime_event_id = d.source_record_id
    JOIN public.dim_equipment e
      ON e.equipment_id = m.equipment_id
    WHERE m.planned_flag IS FALSE
      AND d.planned_flag IS FALSE
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
        date_trunc('month', p.timestamp_start)::date AS month_start,
        p.site_id,
        p.line_id,
        SUM(p.operating_time_min) / 60.0 AS line_operating_hours,
        SUM(p.planned_production_time_min) / 60.0 AS planned_production_hours
    FROM public.fact_production p
    WHERE p.timestamp_start >= TIMESTAMP '2024-01-01'
      AND p.timestamp_start <  TIMESTAMP '2026-01-01'
    GROUP BY
        date_trunc('month', p.timestamp_start)::date,
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

CREATE VIEW analytics.vw_monthly_equipment_type_reliability_trend AS
WITH linked_failure AS (
    SELECT
        date_trunc('month', d.event_start)::date AS month_start,
        d.site_id,
        e.equipment_type,
        e.equipment_id,
        m.duration_hours AS repair_duration_hours,
        d.duration_min / 60.0 AS downtime_hours
    FROM public.fact_maintenance m
    JOIN public.fact_downtime d
      ON m.downtime_event_id = d.source_record_id
    JOIN public.dim_equipment e
      ON e.equipment_id = m.equipment_id
    WHERE m.planned_flag IS FALSE
      AND d.planned_flag IS FALSE
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
