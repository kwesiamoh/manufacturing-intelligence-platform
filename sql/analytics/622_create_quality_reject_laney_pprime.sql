-- Stage 12B.2: Laney p' SPC for reject proportion
-- Replaces the ordinary p-chart as the primary SPC result because the
-- synthetic enterprise data exhibits strong extra-binomial variation.
--
-- Source provenance: SYNTHETIC_ENTERPRISE (synthetic integration data).
-- Baseline: 2024
-- Monitoring: 2025
-- Segmentation: site + line + product
-- Subgroup: production shift

BEGIN;

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.vw_quality_reject_laney_pprime AS
WITH source_rows AS (
    SELECT
        production_id,
        production_record_id,
        timestamp_start,
        timestamp_end,
        date_id,
        EXTRACT(YEAR FROM timestamp_start)::integer AS calendar_year,
        site_code,
        site_name,
        line_code,
        line_name,
        product_code,
        product_name,
        shift_code,
        shift_name,
        actual_quantity::double precision AS subgroup_units,
        reject_quantity::double precision AS reject_units,
        (
            reject_quantity::double precision
            / NULLIF(actual_quantity::double precision, 0)
        ) AS reject_proportion
    FROM gold_bi.vw_shift_manufacturing_performance
    WHERE actual_quantity > 0
      AND reject_quantity >= 0
      AND timestamp_start >= TIMESTAMP '2024-01-01 00:00:00'
      AND timestamp_start <  TIMESTAMP '2026-01-01 00:00:00'
),
baseline_center AS (
    SELECT
        site_code,
        line_code,
        product_code,
        COUNT(*)::bigint AS baseline_subgroup_count,
        SUM(subgroup_units)::double precision AS baseline_units,
        SUM(reject_units)::double precision AS baseline_reject_units,
        (
            SUM(reject_units) / NULLIF(SUM(subgroup_units), 0)
        )::double precision AS p_bar
    FROM source_rows
    WHERE calendar_year = 2024
    GROUP BY site_code, line_code, product_code
),
baseline_z AS (
    SELECT
        s.site_code,
        s.line_code,
        s.product_code,
        s.timestamp_start,
        s.production_id,
        s.reject_proportion,
        b.p_bar,
        CASE
            WHEN b.p_bar IS NULL
              OR b.p_bar <= 0
              OR b.p_bar >= 1
              OR s.subgroup_units <= 0
            THEN NULL
            ELSE
                (
                    s.reject_proportion - b.p_bar
                )
                /
                sqrt(
                    b.p_bar * (1.0 - b.p_bar)
                    / s.subgroup_units
                )
        END::double precision AS z_value
    FROM source_rows s
    JOIN baseline_center b
      ON b.site_code = s.site_code
     AND b.line_code = s.line_code
     AND b.product_code = s.product_code
    WHERE s.calendar_year = 2024
),
baseline_mr AS (
    SELECT
        site_code,
        line_code,
        product_code,
        ABS(
            z_value
            - LAG(z_value) OVER (
                PARTITION BY site_code, line_code, product_code
                ORDER BY timestamp_start, production_id
            )
        )::double precision AS moving_range_z
    FROM baseline_z
    WHERE z_value IS NOT NULL
),
sigma_z AS (
    SELECT
        site_code,
        line_code,
        product_code,
        COUNT(moving_range_z)::bigint AS moving_range_count,
        AVG(moving_range_z)::double precision AS mean_moving_range_z,
        (
            AVG(moving_range_z) / 1.128
        )::double precision AS sigma_z
    FROM baseline_mr
    WHERE moving_range_z IS NOT NULL
    GROUP BY site_code, line_code, product_code
),
scored AS (
    SELECT
        s.*,
        b.baseline_subgroup_count,
        b.baseline_units,
        b.baseline_reject_units,
        b.p_bar,
        z.moving_range_count,
        z.mean_moving_range_z,
        z.sigma_z,
        CASE
            WHEN b.p_bar IS NULL
              OR b.p_bar <= 0
              OR b.p_bar >= 1
              OR s.subgroup_units <= 0
            THEN NULL
            ELSE sqrt(
                b.p_bar * (1.0 - b.p_bar)
                / s.subgroup_units
            )
        END::double precision AS binomial_sigma_p
    FROM source_rows s
    LEFT JOIN baseline_center b
      ON b.site_code = s.site_code
     AND b.line_code = s.line_code
     AND b.product_code = s.product_code
    LEFT JOIN sigma_z z
      ON z.site_code = s.site_code
     AND z.line_code = s.line_code
     AND z.product_code = s.product_code
)
SELECT
    production_id,
    production_record_id,
    timestamp_start,
    timestamp_end,
    date_id,
    calendar_year,
    CASE
        WHEN calendar_year = 2024 THEN 'BASELINE_2024'
        WHEN calendar_year = 2025 THEN 'MONITORING_2025'
        ELSE 'OUT_OF_SCOPE'
    END::text AS spc_phase,
    site_code,
    site_name,
    line_code,
    line_name,
    product_code,
    product_name,
    shift_code,
    shift_name,
    subgroup_units,
    reject_units,
    reject_proportion,
    baseline_subgroup_count,
    baseline_units,
    baseline_reject_units,
    p_bar AS center_line,
    moving_range_count,
    mean_moving_range_z,
    sigma_z,
    binomial_sigma_p,
    CASE
        WHEN p_bar IS NULL OR sigma_z IS NULL OR binomial_sigma_p IS NULL
        THEN NULL
        ELSE GREATEST(
            0.0,
            p_bar - 3.0 * sigma_z * binomial_sigma_p
        )
    END::double precision AS lower_control_limit,
    CASE
        WHEN p_bar IS NULL OR sigma_z IS NULL OR binomial_sigma_p IS NULL
        THEN NULL
        ELSE LEAST(
            1.0,
            p_bar + 3.0 * sigma_z * binomial_sigma_p
        )
    END::double precision AS upper_control_limit,
    CASE
        WHEN p_bar IS NULL
          OR sigma_z IS NULL
          OR sigma_z = 0
          OR binomial_sigma_p IS NULL
          OR binomial_sigma_p = 0
        THEN NULL
        ELSE (
            reject_proportion - p_bar
        ) / (sigma_z * binomial_sigma_p)
    END::double precision AS laney_standardized_z,
    CASE
        WHEN p_bar IS NULL OR sigma_z IS NULL OR binomial_sigma_p IS NULL
            THEN 'NO_BASELINE'
        WHEN reject_proportion >
             LEAST(1.0, p_bar + 3.0 * sigma_z * binomial_sigma_p)
            THEN 'ABOVE_UCL'
        WHEN reject_proportion <
             GREATEST(0.0, p_bar - 3.0 * sigma_z * binomial_sigma_p)
            THEN 'BELOW_LCL'
        ELSE 'IN_CONTROL'
    END::text AS control_status,
    CASE
        WHEN p_bar IS NULL OR sigma_z IS NULL OR binomial_sigma_p IS NULL
            THEN NULL
        WHEN reject_proportion >
             LEAST(1.0, p_bar + 3.0 * sigma_z * binomial_sigma_p)
            THEN TRUE
        WHEN reject_proportion <
             GREATEST(0.0, p_bar - 3.0 * sigma_z * binomial_sigma_p)
            THEN TRUE
        ELSE FALSE
    END AS is_special_cause,
    CASE
        WHEN sigma_z IS NULL THEN NULL
        WHEN sigma_z > 1.0 THEN 'OVERDISPERSED'
        WHEN sigma_z < 1.0 THEN 'UNDERDISPERSED'
        ELSE 'BINOMIAL_EQUIVALENT'
    END::text AS dispersion_status,
    FALSE AS is_real_data,
    'SYNTHETIC_ENTERPRISE'::text AS source_code,
    'Synthetic enterprise integration data; Laney p-prime SPC workflow demonstration only.'::text
        AS provenance_note
FROM scored;

COMMENT ON VIEW analytics.vw_quality_reject_laney_pprime IS
'Laney p-prime chart for shift reject proportions. 2024 fixed baseline, 2025 monitoring. Uses sigma-z from moving ranges of standardized baseline proportions to correct extra-binomial variation. Source is synthetic enterprise integration data.';

COMMIT;
