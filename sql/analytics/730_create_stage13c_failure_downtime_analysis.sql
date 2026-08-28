-- Stage 13C / 16A.6: Failure Mode & Downtime Analysis
-- Source: SYNTHETIC_ENTERPRISE integration layer.
-- Corrective linkage joins the one-row-per-downtime failure-event view, so
-- additional work orders cannot multiply downtime metrics.

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.vw_failure_reason_downtime_summary AS
WITH downtime_base AS (
    SELECT
        d.downtime_id,
        d.site_id,
        d.line_id,
        d.equipment_id,
        d.failure_reason_id,
        d.duration_min,
        d.planned_flag,
        d.production_loss_quantity,
        d.source_dataset_id,
        d.source_record_id,
        CASE WHEN f.downtime_id IS NOT NULL THEN TRUE ELSE FALSE END
            AS corrective_maintenance_linked
    FROM public.fact_downtime d
    LEFT JOIN analytics.vw_corrective_failure_event f
      ON f.downtime_source_dataset_id = d.source_dataset_id
     AND f.downtime_source_record_id = d.source_record_id
),
agg AS (
    SELECT
        site_id,
        failure_reason_id,
        COUNT(*) AS downtime_event_count,
        COUNT(*) FILTER (WHERE planned_flag IS FALSE) AS unplanned_downtime_event_count,
        COUNT(*) FILTER (WHERE corrective_maintenance_linked)
            AS corrective_linked_failure_count,
        SUM(duration_min) AS total_downtime_min,
        SUM(duration_min) FILTER (WHERE planned_flag IS FALSE)
            AS unplanned_downtime_min,
        SUM(duration_min) FILTER (WHERE corrective_maintenance_linked)
            AS corrective_linked_downtime_min,
        SUM(production_loss_quantity) AS total_production_loss_quantity,
        SUM(production_loss_quantity) FILTER (WHERE planned_flag IS FALSE)
            AS unplanned_production_loss_quantity,
        AVG(duration_min) FILTER (WHERE planned_flag IS FALSE)
            AS avg_unplanned_event_duration_min
    FROM downtime_base
    GROUP BY site_id, failure_reason_id
),
ranked AS (
    SELECT
        a.*,
        SUM(unplanned_downtime_min) OVER (
            PARTITION BY site_id
        ) AS site_unplanned_downtime_min,
        ROW_NUMBER() OVER (
            PARTITION BY site_id
            ORDER BY unplanned_downtime_min DESC NULLS LAST
        ) AS pareto_rank,
        SUM(unplanned_downtime_min) OVER (
            PARTITION BY site_id
            ORDER BY unplanned_downtime_min DESC NULLS LAST
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_unplanned_downtime_min
    FROM agg a
)
SELECT
    s.site_code,
    s.site_name,
    fr.failure_category,
    fr.failure_reason,
    fr.planned_flag AS reason_planned_flag,
    r.downtime_event_count,
    r.unplanned_downtime_event_count,
    r.corrective_linked_failure_count,
    r.total_downtime_min,
    r.unplanned_downtime_min,
    r.corrective_linked_downtime_min,
    r.total_production_loss_quantity,
    r.unplanned_production_loss_quantity,
    r.avg_unplanned_event_duration_min,
    r.site_unplanned_downtime_min,
    r.pareto_rank,
    CASE
        WHEN r.site_unplanned_downtime_min > 0
        THEN r.unplanned_downtime_min / r.site_unplanned_downtime_min
    END AS unplanned_downtime_share,
    CASE
        WHEN r.site_unplanned_downtime_min > 0
        THEN r.cumulative_unplanned_downtime_min / r.site_unplanned_downtime_min
    END AS cumulative_unplanned_downtime_share
FROM ranked r
JOIN public.dim_site s
  ON s.site_id = r.site_id
LEFT JOIN public.dim_failure_reason fr
  ON fr.failure_reason_id = r.failure_reason_id;

CREATE OR REPLACE VIEW analytics.vw_equipment_failure_burden AS
SELECT
    k.site_code,
    k.site_name,
    k.line_code,
    k.line_name,
    k.equipment_code,
    k.equipment_name,
    k.equipment_type,
    k.corrective_failure_count,
    k.linked_failure_downtime_hours,
    k.mttr_hours,
    k.mean_calendar_inter_failure_hours,
    k.operating_hours_mtbf_proxy,
    k.corrective_failures_per_1000_line_operating_hours,
    k.reliability_availability_proxy,
    k.total_corrective_maintenance_cost,
    k.linked_production_loss_quantity,
    CASE
        WHEN k.corrective_failure_count > 0
        THEN k.linked_failure_downtime_hours / k.corrective_failure_count
    END AS avg_linked_downtime_h_per_failure,
    DENSE_RANK() OVER (
        ORDER BY k.linked_failure_downtime_hours DESC NULLS LAST
    ) AS enterprise_downtime_burden_rank,
    DENSE_RANK() OVER (
        ORDER BY k.corrective_failure_count DESC NULLS LAST
    ) AS enterprise_failure_frequency_rank
FROM analytics.vw_equipment_reliability_kpi k
WHERE k.corrective_failure_count > 0;
