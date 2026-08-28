-- Stage 12B: Quality reject-proportion SPC (p-chart)
-- Source: SYNTHETIC_ENTERPRISE integration layer.
-- Purpose: portfolio demonstration of statistically appropriate attribute SPC.
--
-- Design:
--   * subgroup = production shift
--   * segmentation = site + line + product
--   * Phase I baseline = calendar year 2024
--   * Phase II monitoring = calendar year 2025
--   * p-bar = pooled 2024 rejects / pooled 2024 actual units
--   * limits = p-bar +/- 3 * sqrt(p-bar * (1-p-bar) / subgroup_n)
--   * limits clipped to [0,1]
--
-- Important:
-- These are analytical control limits, NOT customer specification limits.

BEGIN;

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.vw_quality_reject_pchart AS
WITH source_rows AS (
    SELECT
        production_id,
        production_record_id,
        timestamp_start,
        timestamp_end,
        date_id,
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
        reject_rate::double precision AS source_reject_rate,
        EXTRACT(YEAR FROM timestamp_start)::integer AS calendar_year
    FROM gold_bi.vw_shift_manufacturing_performance
    WHERE actual_quantity > 0
      AND reject_quantity >= 0
      AND timestamp_start >= TIMESTAMP '2024-01-01 00:00:00'
      AND timestamp_start <  TIMESTAMP '2026-01-01 00:00:00'
),
baseline AS (
    SELECT
        site_code,
        line_code,
        product_code,
        COUNT(*)::bigint AS baseline_subgroup_count,
        SUM(subgroup_units)::double precision AS baseline_units,
        SUM(reject_units)::double precision AS baseline_reject_units,
        (
            SUM(reject_units)
            / NULLIF(SUM(subgroup_units), 0)
        )::double precision AS baseline_reject_proportion
    FROM source_rows
    WHERE calendar_year = 2024
    GROUP BY site_code, line_code, product_code
),
scored AS (
    SELECT
        s.*,
        b.baseline_subgroup_count,
        b.baseline_units,
        b.baseline_reject_units,
        b.baseline_reject_proportion,
        (s.reject_units / NULLIF(s.subgroup_units, 0))::double precision
            AS reject_proportion,
        CASE
            WHEN b.baseline_reject_proportion IS NULL THEN NULL
            ELSE sqrt(
                b.baseline_reject_proportion
                * (1.0 - b.baseline_reject_proportion)
                / NULLIF(s.subgroup_units, 0)
            )
        END::double precision AS pchart_sigma
    FROM source_rows s
    LEFT JOIN baseline b
      ON b.site_code = s.site_code
     AND b.line_code = s.line_code
     AND b.product_code = s.product_code
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
    baseline_reject_proportion AS center_line,
    GREATEST(
        0.0,
        baseline_reject_proportion - 3.0 * pchart_sigma
    )::double precision AS lower_control_limit,
    LEAST(
        1.0,
        baseline_reject_proportion + 3.0 * pchart_sigma
    )::double precision AS upper_control_limit,
    CASE
        WHEN pchart_sigma IS NULL OR pchart_sigma = 0 THEN NULL
        ELSE (
            (reject_proportion - baseline_reject_proportion)
            / pchart_sigma
        )::double precision
    END AS standardized_z,
    CASE
        WHEN baseline_reject_proportion IS NULL THEN 'NO_BASELINE'
        WHEN reject_proportion >
             LEAST(1.0, baseline_reject_proportion + 3.0 * pchart_sigma)
            THEN 'ABOVE_UCL'
        WHEN reject_proportion <
             GREATEST(0.0, baseline_reject_proportion - 3.0 * pchart_sigma)
            THEN 'BELOW_LCL'
        ELSE 'IN_CONTROL'
    END::text AS control_status,
    CASE
        WHEN baseline_reject_proportion IS NULL THEN NULL
        WHEN reject_proportion >
             LEAST(1.0, baseline_reject_proportion + 3.0 * pchart_sigma)
            THEN TRUE
        WHEN reject_proportion <
             GREATEST(0.0, baseline_reject_proportion - 3.0 * pchart_sigma)
            THEN TRUE
        ELSE FALSE
    END AS is_special_cause,
    FALSE AS is_real_data,
    'SYNTHETIC_ENTERPRISE'::text AS source_code,
    'Synthetic enterprise integration data; SPC workflow demonstration only.'::text
        AS provenance_note
FROM scored;

COMMENT ON VIEW analytics.vw_quality_reject_pchart IS
'Stage 12B p-chart for shift reject proportions. 2024 is the fixed Phase I baseline; 2025 is Phase II monitoring. Source is synthetic enterprise integration data, not measured plant history.';

COMMIT;
