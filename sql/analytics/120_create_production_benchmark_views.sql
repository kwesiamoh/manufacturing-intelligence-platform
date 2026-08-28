-- production benchmark — Production benchmarking, Pareto, changeover and utilization analytics.

CREATE OR REPLACE VIEW vw_line_performance_summary AS
SELECT
    site_code,
    site_name,
    line_code,
    line_name,

    COUNT(*) AS shift_count,
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
    END AS good_output_attainment,

    CASE
        WHEN SUM(planned_production_time_min * nominal_rate) > 0
        THEN SUM(actual_quantity) /
             (SUM(planned_production_time_min * nominal_rate) / 60.0)
    END AS gross_capacity_utilization,

    CASE
        WHEN SUM(planned_production_time_min) > 0
        THEN SUM(actual_quantity) /
             (SUM(planned_production_time_min) / 60.0)
    END AS scheduled_throughput_per_hour

FROM vw_shift_production_kpi
GROUP BY
    site_code,
    site_name,
    line_code,
    line_name;


CREATE OR REPLACE VIEW vw_line_performance_rank AS
SELECT
    *,
    DENSE_RANK() OVER (ORDER BY oee DESC) AS enterprise_oee_rank,
    DENSE_RANK() OVER (
        PARTITION BY site_code
        ORDER BY oee DESC
    ) AS site_oee_rank,
    DENSE_RANK() OVER (
        ORDER BY production_attainment DESC
    ) AS enterprise_attainment_rank
FROM vw_line_performance_summary;


CREATE OR REPLACE VIEW vw_downtime_reason_pareto AS
WITH src AS (
    SELECT source_dataset_id
    FROM dim_source_dataset
    WHERE source_code = 'SYNTHETIC_ENTERPRISE'
),
reason_totals AS (
    SELECT
        s.site_code,
        s.site_name,
        fr.failure_category,
        fr.failure_reason,
        d.planned_flag,
        COUNT(*) AS event_count,
        SUM(d.duration_min) AS downtime_min
    FROM fact_downtime d
    JOIN src x
      ON x.source_dataset_id = d.source_dataset_id
    JOIN dim_site s
      ON s.site_id = d.site_id
    LEFT JOIN dim_failure_reason fr
      ON fr.failure_reason_id = d.failure_reason_id
    GROUP BY
        s.site_code,
        s.site_name,
        fr.failure_category,
        fr.failure_reason,
        d.planned_flag
),
ranked AS (
    SELECT
        *,
        SUM(downtime_min) OVER (
            PARTITION BY site_code
        ) AS site_total_downtime_min,

        SUM(downtime_min) OVER (
            PARTITION BY site_code
            ORDER BY downtime_min DESC, failure_reason
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_downtime_min,

        ROW_NUMBER() OVER (
            PARTITION BY site_code
            ORDER BY downtime_min DESC, failure_reason
        ) AS pareto_rank
    FROM reason_totals
)
SELECT
    *,
    CASE
        WHEN site_total_downtime_min > 0
        THEN downtime_min / site_total_downtime_min
    END AS downtime_share,

    CASE
        WHEN site_total_downtime_min > 0
        THEN cumulative_downtime_min / site_total_downtime_min
    END AS cumulative_downtime_share

FROM ranked;


CREATE OR REPLACE VIEW vw_changeover_summary AS
WITH src AS (
    SELECT source_dataset_id
    FROM dim_source_dataset
    WHERE source_code = 'SYNTHETIC_ENTERPRISE'
),
changeovers AS (
    SELECT
        s.site_code,
        s.site_name,
        l.line_code,
        l.line_name,
        COUNT(*) AS changeover_event_count,
        SUM(d.duration_min) AS total_changeover_min,
        AVG(d.duration_min) AS avg_changeover_min,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY d.duration_min)
            AS median_changeover_min,
        MIN(d.duration_min) AS min_changeover_min,
        MAX(d.duration_min) AS max_changeover_min
    FROM fact_downtime d
    JOIN src x
      ON x.source_dataset_id = d.source_dataset_id
    JOIN dim_site s
      ON s.site_id = d.site_id
    JOIN dim_line l
      ON l.line_id = d.line_id
    JOIN dim_failure_reason fr
      ON fr.failure_reason_id = d.failure_reason_id
    WHERE d.planned_flag = TRUE
      AND fr.failure_category = 'CHANGEOVER'
    GROUP BY
        s.site_code,
        s.site_name,
        l.line_code,
        l.line_name
)
SELECT
    *,
    DENSE_RANK() OVER (
        ORDER BY avg_changeover_min ASC
    ) AS enterprise_changeover_rank,
    DENSE_RANK() OVER (
        PARTITION BY site_code
        ORDER BY avg_changeover_min ASC
    ) AS site_changeover_rank
FROM changeovers;


CREATE OR REPLACE VIEW vw_site_production_benchmark AS
SELECT
    site_code,
    site_name,
    COUNT(*) AS line_count,

    AVG(oee) AS avg_line_oee,
    MIN(oee) AS min_line_oee,
    MAX(oee) AS max_line_oee,

    AVG(production_attainment) AS avg_line_production_attainment,
    AVG(good_output_attainment) AS avg_line_good_output_attainment,
    AVG(gross_capacity_utilization) AS avg_line_gross_capacity_utilization,

    SUM(planned_quantity) AS planned_quantity,
    SUM(actual_quantity) AS actual_quantity,
    SUM(good_quantity) AS good_quantity,
    SUM(reject_quantity) AS reject_quantity

FROM vw_line_performance_summary
GROUP BY site_code, site_name;


CREATE OR REPLACE VIEW vw_site_production_rank AS
SELECT
    *,
    DENSE_RANK() OVER (
        ORDER BY avg_line_oee DESC
    ) AS oee_rank,
    DENSE_RANK() OVER (
        ORDER BY avg_line_production_attainment DESC
    ) AS attainment_rank,
    DENSE_RANK() OVER (
        ORDER BY avg_line_gross_capacity_utilization DESC
    ) AS utilization_rank
FROM vw_site_production_benchmark;
