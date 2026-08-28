-- Stage 13B / 16A.6: Equipment Reliability KPI layer
-- Source: SYNTHETIC_ENTERPRISE integration layer
--
-- Grain rules:
--   * vw_corrective_maintenance_downtime_link: one row per maintenance row.
--   * vw_corrective_failure_event: one row per source-qualified downtime event.
--   * failure counts and downtime use failure-event grain.
--   * repair duration and maintenance cost originate at work-order grain and
--     are aggregated once into their linked failure event.

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.vw_corrective_maintenance_downtime_link AS
SELECT
    m.maintenance_id,
    m.source_dataset_id AS maintenance_source_dataset_id,
    m.source_record_id AS maintenance_source_record_id,
    m.work_order_id,
    m.equipment_id AS maintenance_equipment_id,
    m.start_timestamp AS repair_start,
    m.end_timestamp AS repair_end,
    m.duration_hours AS repair_duration_hours,
    m.total_cost AS maintenance_cost,
    m.failure_reason_id AS maintenance_failure_reason_id,
    m.downtime_source_dataset_id,
    m.downtime_event_id AS downtime_source_record_id,
    d.downtime_id,
    d.site_id AS downtime_site_id,
    d.line_id AS downtime_line_id,
    d.equipment_id AS downtime_equipment_id,
    d.failure_reason_id AS downtime_failure_reason_id,
    d.event_start AS failure_start,
    d.event_end AS failure_end,
    d.duration_min AS failure_downtime_min,
    d.production_loss_quantity,
    d.production_record_id,
    d.planned_flag AS downtime_planned_flag
FROM public.fact_maintenance m
JOIN public.fact_downtime d
  ON d.source_dataset_id = m.downtime_source_dataset_id
 AND d.source_record_id = m.downtime_event_id
WHERE m.planned_flag IS FALSE
  AND d.planned_flag IS FALSE;

CREATE OR REPLACE VIEW analytics.vw_corrective_failure_event AS
SELECT
    l.downtime_source_dataset_id,
    l.downtime_source_record_id,
    l.downtime_id,
    l.downtime_site_id AS site_id,
    l.downtime_line_id AS line_id,
    l.downtime_equipment_id AS equipment_id,
    l.downtime_failure_reason_id AS failure_reason_id,
    l.failure_start,
    l.failure_end,
    l.failure_downtime_min / 60.0 AS failure_downtime_hours,
    l.production_loss_quantity,
    l.production_record_id,
    COUNT(*) AS maintenance_work_order_count,
    MIN(l.repair_start) AS first_repair_start,
    MAX(l.repair_end) AS last_repair_end,
    SUM(l.repair_duration_hours) AS total_repair_duration_hours,
    AVG(l.repair_duration_hours) AS avg_work_order_repair_duration_hours,
    SUM(l.maintenance_cost) AS total_corrective_maintenance_cost,
    COUNT(DISTINCT l.maintenance_equipment_id)
        AS maintenance_equipment_count
FROM analytics.vw_corrective_maintenance_downtime_link l
GROUP BY
    l.downtime_source_dataset_id,
    l.downtime_source_record_id,
    l.downtime_id,
    l.downtime_site_id,
    l.downtime_line_id,
    l.downtime_equipment_id,
    l.downtime_failure_reason_id,
    l.failure_start,
    l.failure_end,
    l.failure_downtime_min,
    l.production_loss_quantity,
    l.production_record_id;

CREATE OR REPLACE VIEW analytics.vw_equipment_reliability_kpi AS
WITH failure_sequence AS (
    SELECT
        f.*,
        LAG(f.failure_start) OVER (
            PARTITION BY f.equipment_id
            ORDER BY
                f.failure_start,
                f.downtime_source_dataset_id,
                f.downtime_source_record_id
        ) AS prior_failure_start
    FROM analytics.vw_corrective_failure_event f
),
failure_stats AS (
    SELECT
        equipment_id,
        COUNT(*) AS corrective_failure_count,
        SUM(maintenance_work_order_count) AS corrective_work_order_count,
        MIN(failure_start) AS first_failure_start,
        MAX(failure_start) AS last_failure_start,
        SUM(failure_downtime_hours) AS linked_failure_downtime_hours,
        AVG(failure_downtime_hours) AS avg_failure_downtime_hours,
        AVG(total_repair_duration_hours) AS mttr_hours,
        PERCENTILE_CONT(0.5) WITHIN GROUP (
            ORDER BY total_repair_duration_hours
        ) AS median_repair_duration_hours,
        SUM(total_repair_duration_hours) AS total_corrective_repair_hours,
        SUM(total_corrective_maintenance_cost)
            AS total_corrective_maintenance_cost,
        SUM(production_loss_quantity) AS linked_production_loss_quantity,
        AVG(
            EXTRACT(EPOCH FROM (failure_start - prior_failure_start)) / 3600.0
        ) FILTER (WHERE prior_failure_start IS NOT NULL)
          AS mean_calendar_inter_failure_hours,
        PERCENTILE_CONT(0.5) WITHIN GROUP (
            ORDER BY EXTRACT(EPOCH FROM (failure_start - prior_failure_start)) / 3600.0
        ) FILTER (WHERE prior_failure_start IS NOT NULL)
          AS median_calendar_inter_failure_hours
    FROM failure_sequence
    GROUP BY equipment_id
),
line_exposure AS (
    SELECT
        p.line_id,
        SUM(p.operating_time_min) / 60.0 AS line_operating_hours,
        SUM(p.planned_production_time_min) / 60.0 AS line_planned_production_hours
    FROM public.fact_production p
    WHERE p.timestamp_start >= TIMESTAMP '2024-01-01'
      AND p.timestamp_start <  TIMESTAMP '2026-01-01'
    GROUP BY p.line_id
)
SELECT
    e.equipment_id,
    s.site_code,
    s.site_name,
    l.line_code,
    l.line_name,
    e.equipment_code,
    e.equipment_name,
    e.equipment_type,
    e.criticality_class,
    e.active_flag,
    fs.corrective_failure_count,
    fs.first_failure_start,
    fs.last_failure_start,
    fs.linked_failure_downtime_hours,
    fs.avg_failure_downtime_hours,
    fs.mttr_hours,
    fs.median_repair_duration_hours,
    fs.total_corrective_repair_hours,
    fs.total_corrective_maintenance_cost,
    fs.linked_production_loss_quantity,
    fs.mean_calendar_inter_failure_hours,
    fs.median_calendar_inter_failure_hours,
    le.line_operating_hours,
    le.line_planned_production_hours,
    CASE
        WHEN le.line_operating_hours IS NOT NULL
         AND fs.corrective_failure_count > 0
        THEN le.line_operating_hours / fs.corrective_failure_count
    END AS operating_hours_mtbf_proxy,
    CASE
        WHEN le.line_operating_hours IS NOT NULL
         AND le.line_operating_hours > 0
         AND fs.corrective_failure_count > 0
        THEN fs.corrective_failure_count * 1000.0 / le.line_operating_hours
    END AS corrective_failures_per_1000_line_operating_hours,
    CASE
        WHEN le.line_operating_hours IS NOT NULL
         AND fs.corrective_failure_count > 0
         AND fs.mttr_hours IS NOT NULL
        THEN
            (le.line_operating_hours / fs.corrective_failure_count)
            /
            (
                (le.line_operating_hours / fs.corrective_failure_count)
                + fs.mttr_hours
            )
    END AS reliability_availability_proxy,
    CASE
        WHEN fs.corrective_failure_count > 0
        THEN fs.linked_failure_downtime_hours / fs.corrective_failure_count
    END AS mean_linked_downtime_per_failure_hours,
    e.source_dataset_id,
    fs.corrective_work_order_count,
    CASE
        WHEN fs.corrective_failure_count > 0
        THEN fs.corrective_work_order_count::numeric
             / fs.corrective_failure_count
    END AS avg_work_orders_per_failure
FROM public.dim_equipment e
LEFT JOIN failure_stats fs
  ON fs.equipment_id = e.equipment_id
LEFT JOIN line_exposure le
  ON le.line_id = e.line_id
LEFT JOIN public.dim_line l
  ON l.line_id = e.line_id
LEFT JOIN public.dim_site s
  ON s.site_id = COALESCE(l.site_id, (
      SELECT m.site_id
      FROM public.fact_maintenance m
      WHERE m.equipment_id = e.equipment_id
      ORDER BY m.start_timestamp
      LIMIT 1
  ));

CREATE OR REPLACE VIEW analytics.vw_equipment_type_reliability_summary AS
SELECT
    site_code,
    site_name,
    equipment_type,
    COUNT(*) FILTER (WHERE corrective_failure_count > 0) AS equipment_with_failures,
    SUM(corrective_failure_count) AS corrective_failure_count,
    SUM(linked_failure_downtime_hours) AS linked_failure_downtime_hours,
    AVG(mttr_hours) FILTER (WHERE corrective_failure_count > 0) AS avg_equipment_mttr_hours,
    AVG(mean_calendar_inter_failure_hours)
        FILTER (WHERE corrective_failure_count > 1)
        AS avg_equipment_calendar_inter_failure_hours,
    AVG(operating_hours_mtbf_proxy)
        FILTER (WHERE operating_hours_mtbf_proxy IS NOT NULL)
        AS avg_operating_hours_mtbf_proxy,
    AVG(corrective_failures_per_1000_line_operating_hours)
        FILTER (WHERE corrective_failures_per_1000_line_operating_hours IS NOT NULL)
        AS avg_failures_per_1000_line_operating_hours,
    AVG(reliability_availability_proxy)
        FILTER (WHERE reliability_availability_proxy IS NOT NULL)
        AS avg_reliability_availability_proxy,
    SUM(total_corrective_maintenance_cost) AS total_corrective_maintenance_cost,
    SUM(linked_production_loss_quantity) AS linked_production_loss_quantity,
    SUM(corrective_work_order_count) AS corrective_work_order_count
FROM analytics.vw_equipment_reliability_kpi
GROUP BY site_code, site_name, equipment_type;
