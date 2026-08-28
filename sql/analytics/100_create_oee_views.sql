-- Stage 5A — Production and OEE analytics
-- Source: validated SYNTHETIC_ENTERPRISE production/downtime/quality facts.

CREATE OR REPLACE VIEW vw_shift_production_kpi AS
WITH src AS (
    SELECT source_dataset_id
    FROM dim_source_dataset
    WHERE source_code = 'SYNTHETIC_ENTERPRISE'
),
base AS (
    SELECT
        p.production_id,
        p.source_record_id AS production_record_id,
        p.timestamp_start,
        p.timestamp_end,
        p.date_id,
        s.site_code,
        s.site_name,
        l.line_code,
        l.line_name,
        pr.product_code,
        pr.product_name,
        sh.shift_code,
        sh.shift_name,
        p.planned_quantity,
        p.actual_quantity,
        p.good_quantity,
        p.reject_quantity,
        p.nominal_rate,
        p.actual_rate,
        p.operating_time_min,
        p.planned_production_time_min,

        CASE
            WHEN p.planned_production_time_min > 0
            THEN p.operating_time_min / p.planned_production_time_min
        END AS availability,

        CASE
            WHEN p.operating_time_min > 0
             AND p.nominal_rate > 0
            THEN p.actual_quantity /
                 ((p.operating_time_min / 60.0) * p.nominal_rate)
        END AS performance,

        CASE
            WHEN p.actual_quantity > 0
            THEN p.good_quantity::numeric / p.actual_quantity
        END AS quality,

        CASE
            WHEN p.planned_quantity > 0
            THEN p.actual_quantity::numeric / p.planned_quantity
        END AS production_attainment,

        CASE
            WHEN p.planned_quantity > 0
            THEN p.good_quantity::numeric / p.planned_quantity
        END AS good_output_attainment,

        CASE
            WHEN p.planned_production_time_min > 0
            THEN p.actual_quantity /
                 (p.planned_production_time_min / 60.0)
        END AS scheduled_throughput_per_hour,

        CASE
            WHEN p.operating_time_min > 0
            THEN p.actual_quantity /
                 (p.operating_time_min / 60.0)
        END AS running_throughput_per_hour,

        CASE
            WHEN p.actual_quantity > 0
            THEN p.reject_quantity::numeric / p.actual_quantity
        END AS reject_rate

    FROM fact_production p
    JOIN src x
      ON x.source_dataset_id = p.source_dataset_id
    JOIN dim_site s
      ON s.site_id = p.site_id
    JOIN dim_line l
      ON l.line_id = p.line_id
    JOIN dim_product pr
      ON pr.product_id = p.product_id
    JOIN dim_shift sh
      ON sh.shift_id = p.shift_id
)
SELECT
    *,
    availability * performance * quality AS oee
FROM base;


CREATE OR REPLACE VIEW vw_shift_production_loss AS
WITH src AS (
    SELECT source_dataset_id
    FROM dim_source_dataset
    WHERE source_code = 'SYNTHETIC_ENTERPRISE'
),
downtime AS (
    SELECT
        d.production_record_id,
        SUM(CASE WHEN d.planned_flag THEN d.duration_min ELSE 0 END) AS planned_downtime_min,
        SUM(CASE WHEN NOT d.planned_flag THEN d.duration_min ELSE 0 END) AS unplanned_downtime_min,
        SUM(
            CASE
                WHEN d.planned_flag
                 AND fr.failure_category = 'CHANGEOVER'
                THEN d.duration_min
                ELSE 0
            END
        ) AS changeover_downtime_min
    FROM fact_downtime d
    JOIN src x
      ON x.source_dataset_id = d.source_dataset_id
    LEFT JOIN dim_failure_reason fr
      ON fr.failure_reason_id = d.failure_reason_id
    GROUP BY d.production_record_id
),
base AS (
    SELECT
        k.*,
        COALESCE(dt.planned_downtime_min, 0) AS planned_downtime_min,
        COALESCE(dt.unplanned_downtime_min, 0) AS unplanned_downtime_min,
        COALESCE(dt.changeover_downtime_min, 0) AS changeover_downtime_min
    FROM vw_shift_production_kpi k
    LEFT JOIN downtime dt
      ON dt.production_record_id = k.production_record_id
)
SELECT
    *,
    planned_downtime_min * nominal_rate / 60.0 AS planned_downtime_loss_units,
    unplanned_downtime_min * nominal_rate / 60.0 AS unplanned_downtime_loss_units,
    changeover_downtime_min * nominal_rate / 60.0 AS changeover_loss_units,

    GREATEST(
        ((operating_time_min / 60.0) * nominal_rate) - actual_quantity,
        0
    ) AS speed_loss_units,

    reject_quantity::numeric AS quality_loss_units,

    GREATEST(planned_quantity - good_quantity, 0)::numeric AS total_good_output_gap_units
FROM base;


CREATE OR REPLACE VIEW vw_line_daily_kpi AS
SELECT
    date_id,
    site_code,
    site_name,
    line_code,
    line_name,

    SUM(planned_quantity) AS planned_quantity,
    SUM(actual_quantity) AS actual_quantity,
    SUM(good_quantity) AS good_quantity,
    SUM(reject_quantity) AS reject_quantity,
    SUM(operating_time_min) AS operating_time_min,
    SUM(planned_production_time_min) AS planned_production_time_min,

    CASE
        WHEN SUM(planned_production_time_min) > 0
        THEN SUM(operating_time_min) / SUM(planned_production_time_min)
    END AS availability,

    CASE
        WHEN SUM(operating_time_min * nominal_rate) > 0
        THEN SUM(actual_quantity) /
             (SUM(operating_time_min * nominal_rate) / 60.0)
    END AS performance,

    CASE
        WHEN SUM(actual_quantity) > 0
        THEN SUM(good_quantity)::numeric / SUM(actual_quantity)
    END AS quality,

    (
        CASE
            WHEN SUM(planned_production_time_min) > 0
            THEN SUM(operating_time_min) / SUM(planned_production_time_min)
        END
    )
    *
    (
        CASE
            WHEN SUM(operating_time_min * nominal_rate) > 0
            THEN SUM(actual_quantity) /
                 (SUM(operating_time_min * nominal_rate) / 60.0)
        END
    )
    *
    (
        CASE
            WHEN SUM(actual_quantity) > 0
            THEN SUM(good_quantity)::numeric / SUM(actual_quantity)
        END
    ) AS oee,

    CASE
        WHEN SUM(planned_quantity) > 0
        THEN SUM(actual_quantity)::numeric / SUM(planned_quantity)
    END AS production_attainment,

    CASE
        WHEN SUM(planned_quantity) > 0
        THEN SUM(good_quantity)::numeric / SUM(planned_quantity)
    END AS good_output_attainment

FROM vw_shift_production_kpi
GROUP BY
    date_id,
    site_code,
    site_name,
    line_code,
    line_name;


CREATE OR REPLACE VIEW vw_site_daily_kpi AS
SELECT
    date_id,
    site_code,
    site_name,

    SUM(planned_quantity) AS planned_quantity,
    SUM(actual_quantity) AS actual_quantity,
    SUM(good_quantity) AS good_quantity,
    SUM(reject_quantity) AS reject_quantity,
    SUM(operating_time_min) AS operating_time_min,
    SUM(planned_production_time_min) AS planned_production_time_min,

    CASE
        WHEN SUM(planned_production_time_min) > 0
        THEN SUM(operating_time_min) / SUM(planned_production_time_min)
    END AS availability,

    CASE
        WHEN SUM(operating_time_min * nominal_rate) > 0
        THEN SUM(actual_quantity) /
             (SUM(operating_time_min * nominal_rate) / 60.0)
    END AS performance,

    CASE
        WHEN SUM(actual_quantity) > 0
        THEN SUM(good_quantity)::numeric / SUM(actual_quantity)
    END AS quality,

    (
        CASE
            WHEN SUM(planned_production_time_min) > 0
            THEN SUM(operating_time_min) / SUM(planned_production_time_min)
        END
    )
    *
    (
        CASE
            WHEN SUM(operating_time_min * nominal_rate) > 0
            THEN SUM(actual_quantity) /
                 (SUM(operating_time_min * nominal_rate) / 60.0)
        END
    )
    *
    (
        CASE
            WHEN SUM(actual_quantity) > 0
            THEN SUM(good_quantity)::numeric / SUM(actual_quantity)
        END
    ) AS oee,

    CASE
        WHEN SUM(planned_quantity) > 0
        THEN SUM(actual_quantity)::numeric / SUM(planned_quantity)
    END AS production_attainment

FROM vw_shift_production_kpi
GROUP BY
    date_id,
    site_code,
    site_name;
