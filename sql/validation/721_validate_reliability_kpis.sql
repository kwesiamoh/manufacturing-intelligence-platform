-- reliability KPI validation

\pset pager off

\echo '=== 1. Reliability KPI view row count ==='
SELECT COUNT(*) AS equipment_rows
FROM analytics.vw_equipment_reliability_kpi;

\echo ''
\echo '=== 2. Failure population reconciliation ==='
SELECT
    SUM(corrective_failure_count) AS linked_corrective_failures,
    SUM(corrective_work_order_count) AS linked_corrective_work_orders,
    SUM(linked_failure_downtime_hours) AS linked_failure_downtime_hours,
    SUM(total_corrective_repair_hours) AS corrective_repair_hours
FROM analytics.vw_equipment_reliability_kpi;

\echo ''
\echo '=== 3. KPI coverage ==='
SELECT
    COUNT(*) AS equipment_rows,
    COUNT(*) FILTER (WHERE corrective_failure_count > 0) AS equipment_with_failures,
    COUNT(*) FILTER (WHERE mttr_hours IS NOT NULL) AS equipment_with_mttr,
    COUNT(*) FILTER (WHERE mean_calendar_inter_failure_hours IS NOT NULL)
        AS equipment_with_inter_failure_interval,
    COUNT(*) FILTER (WHERE operating_hours_mtbf_proxy IS NOT NULL)
        AS equipment_with_mtbf_proxy,
    COUNT(*) FILTER (WHERE reliability_availability_proxy IS NOT NULL)
        AS equipment_with_availability_proxy
FROM analytics.vw_equipment_reliability_kpi;

\echo ''
\echo '=== 4. KPI sanity ==='
SELECT
    COUNT(*) FILTER (WHERE mttr_hours <= 0) AS invalid_mttr,
    COUNT(*) FILTER (WHERE mean_calendar_inter_failure_hours <= 0)
        AS invalid_inter_failure_interval,
    COUNT(*) FILTER (WHERE operating_hours_mtbf_proxy <= 0)
        AS invalid_mtbf_proxy,
    COUNT(*) FILTER (
        WHERE reliability_availability_proxy < 0
           OR reliability_availability_proxy > 1
    ) AS invalid_availability_proxy
FROM analytics.vw_equipment_reliability_kpi;

\echo ''
\echo '=== 5. Enterprise summary ==='
SELECT
    SUM(corrective_failure_count) AS corrective_failures,
    ROUND(SUM(linked_failure_downtime_hours)::numeric, 2)
        AS linked_downtime_hours,
    ROUND(
        (
            SUM(total_corrective_repair_hours)
            / NULLIF(SUM(corrective_failure_count),0)
        )::numeric,
        4
    ) AS event_weighted_mttr_hours,
    ROUND(
        AVG(mean_calendar_inter_failure_hours)
        FILTER (WHERE mean_calendar_inter_failure_hours IS NOT NULL)::numeric,
        2
    ) AS avg_equipment_calendar_inter_failure_hours,
    ROUND(
        AVG(operating_hours_mtbf_proxy)
        FILTER (WHERE operating_hours_mtbf_proxy IS NOT NULL)::numeric,
        2
    ) AS avg_equipment_operating_hours_mtbf_proxy,
    ROUND(
        AVG(reliability_availability_proxy)
        FILTER (WHERE reliability_availability_proxy IS NOT NULL)::numeric,
        6
    ) AS avg_equipment_reliability_availability_proxy
FROM analytics.vw_equipment_reliability_kpi;

\echo ''
\echo '=== 6. Reliability by equipment type ==='
SELECT
    equipment_type,
    SUM(equipment_with_failures) AS equipment_with_failures,
    SUM(corrective_failure_count) AS corrective_failures,
    ROUND(SUM(linked_failure_downtime_hours)::numeric,2)
        AS downtime_hours,
    ROUND(AVG(avg_equipment_mttr_hours)::numeric,4) AS avg_mttr_h,
    ROUND(AVG(avg_equipment_calendar_inter_failure_hours)::numeric,2)
        AS avg_calendar_inter_failure_h,
    ROUND(AVG(avg_operating_hours_mtbf_proxy)::numeric,2)
        AS avg_operating_mtbf_proxy_h,
    ROUND(AVG(avg_reliability_availability_proxy)::numeric,6)
        AS avg_availability_proxy
FROM analytics.vw_equipment_type_reliability_summary
GROUP BY equipment_type
ORDER BY corrective_failures DESC NULLS LAST;

\echo ''
\echo '=== 7. Highest failure-frequency equipment ==='
SELECT
    site_code,
    line_code,
    equipment_code,
    equipment_type,
    corrective_failure_count,
    ROUND(mttr_hours::numeric,4) AS mttr_h,
    ROUND(mean_calendar_inter_failure_hours::numeric,2)
        AS mean_calendar_inter_failure_h,
    ROUND(operating_hours_mtbf_proxy::numeric,2)
        AS operating_mtbf_proxy_h,
    ROUND(corrective_failures_per_1000_line_operating_hours::numeric,3)
        AS failures_per_1000_operating_h
FROM analytics.vw_equipment_reliability_kpi
WHERE corrective_failure_count > 0
ORDER BY corrective_failure_count DESC, equipment_code
LIMIT 20;

\echo ''
\echo '=== 8. Provenance ==='
SELECT
    k.source_dataset_id,
    s.source_code,
    s.source_name,
    s.integration_role,
    s.is_real_data,
    COUNT(*) AS equipment_rows
FROM analytics.vw_equipment_reliability_kpi k
LEFT JOIN public.dim_source_dataset s
  ON s.source_dataset_id = k.source_dataset_id
GROUP BY
    k.source_dataset_id,
    s.source_code,
    s.source_name,
    s.integration_role,
    s.is_real_data;

\echo ''
\echo '=== 9. Source-qualified maintenance/downtime cardinality ==='
WITH maintenance_per_downtime AS (
    SELECT
        d.source_dataset_id,
        d.source_record_id,
        COUNT(l.maintenance_id) AS maintenance_rows
    FROM public.fact_downtime d
    LEFT JOIN analytics.vw_corrective_maintenance_downtime_link l
      ON l.downtime_source_dataset_id = d.source_dataset_id
     AND l.downtime_source_record_id = d.source_record_id
    GROUP BY d.source_dataset_id, d.source_record_id
)
SELECT
    (SELECT COUNT(*) FROM public.fact_maintenance WHERE planned_flag IS FALSE)
        AS corrective_maintenance_rows,
    COUNT(*) FILTER (WHERE maintenance_rows = 0) AS downtime_events_linked_to_0,
    COUNT(*) FILTER (WHERE maintenance_rows = 1) AS downtime_events_linked_to_1,
    COUNT(*) FILTER (WHERE maintenance_rows > 1) AS downtime_events_linked_to_more_than_1,
    MAX(maintenance_rows) AS max_maintenance_rows_per_downtime
FROM maintenance_per_downtime;

\echo ''
\echo '=== 10. Text-ID collision exposure (informational) ==='
WITH downtime_id_collision AS (
    SELECT source_record_id
    FROM public.fact_downtime
    WHERE source_record_id IS NOT NULL
    GROUP BY source_record_id
    HAVING COUNT(DISTINCT source_dataset_id) > 1
),
raw_ambiguous_maintenance AS (
    SELECT m.maintenance_id
    FROM public.fact_maintenance m
    JOIN public.fact_downtime d
      ON d.source_record_id = m.downtime_event_id
    WHERE m.planned_flag IS FALSE
    GROUP BY m.maintenance_id
    HAVING COUNT(*) > 1
)
SELECT
    (SELECT COUNT(*) FROM downtime_id_collision)
        AS text_ids_reused_across_sources,
    (SELECT COUNT(*) FROM raw_ambiguous_maintenance)
        AS maintenance_links_ambiguous_without_source_qualification;

\echo ''
\echo '=== reliability KPI validation complete ==='

\echo '=== Mandatory reliability KPI gate ==='
DO $validation$
DECLARE
    bad_count bigint;
    expected_work_orders bigint;
    expected_failure_events bigint;
    expected_downtime_hours numeric;
    expected_repair_hours numeric;
    observed_failure_events bigint;
    observed_work_orders bigint;
    observed_downtime_hours numeric;
    observed_repair_hours numeric;
BEGIN
    -- Every corrective maintenance row must resolve to exactly one unplanned
    -- downtime event by the explicit composite lineage key.  Text-only matches
    -- are deliberately not used here.
    SELECT COUNT(*) INTO bad_count
    FROM (
        SELECT m.maintenance_id
        FROM public.fact_maintenance m
        LEFT JOIN public.fact_downtime d
          ON d.source_dataset_id = m.downtime_source_dataset_id
         AND d.source_record_id = m.downtime_event_id
         AND d.planned_flag IS FALSE
        WHERE m.planned_flag IS FALSE
        GROUP BY m.maintenance_id
        HAVING COUNT(d.downtime_id) <> 1
    ) invalid_link;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'reliability KPI found % corrective maintenance rows without exactly one source-qualified unplanned downtime parent', bad_count;
    END IF;

    SELECT
        COUNT(*),
        COUNT(DISTINCT (d.source_dataset_id, d.source_record_id)),
        SUM(m.duration_hours)
    INTO
        expected_work_orders,
        expected_failure_events,
        expected_repair_hours
    FROM public.fact_maintenance m
    JOIN public.fact_downtime d
      ON d.source_dataset_id = m.downtime_source_dataset_id
     AND d.source_record_id = m.downtime_event_id
    WHERE m.planned_flag IS FALSE
      AND d.planned_flag IS FALSE;

    SELECT COALESCE(SUM(d.duration_min) / 60.0, 0)
    INTO expected_downtime_hours
    FROM public.fact_downtime d
    WHERE d.planned_flag IS FALSE
      AND EXISTS (
          SELECT 1
          FROM public.fact_maintenance m
          WHERE m.planned_flag IS FALSE
            AND m.downtime_source_dataset_id = d.source_dataset_id
            AND m.downtime_event_id = d.source_record_id
      );

    IF (SELECT COUNT(*) FROM analytics.vw_corrective_maintenance_downtime_link)
       <> expected_work_orders
       OR (SELECT COUNT(DISTINCT maintenance_id)
           FROM analytics.vw_corrective_maintenance_downtime_link)
       <> expected_work_orders THEN
        RAISE EXCEPTION 'reliability KPI work-order-grain lineage view does not reconcile to qualified maintenance links';
    END IF;

    SELECT
        COUNT(*),
        COALESCE(SUM(maintenance_work_order_count), 0),
        COALESCE(SUM(failure_downtime_hours), 0),
        COALESCE(SUM(total_repair_duration_hours), 0)
    INTO
        observed_failure_events,
        observed_work_orders,
        observed_downtime_hours,
        observed_repair_hours
    FROM analytics.vw_corrective_failure_event;

    IF observed_failure_events <> expected_failure_events
       OR observed_work_orders <> expected_work_orders THEN
        RAISE EXCEPTION 'reliability KPI failure-event/work-order grains do not reconcile: events %/%; work orders %/%', observed_failure_events, expected_failure_events, observed_work_orders, expected_work_orders;
    END IF;
    IF ABS(observed_downtime_hours - expected_downtime_hours) > 0.000001
       OR ABS(observed_repair_hours - expected_repair_hours) > 0.000001 THEN
        RAISE EXCEPTION 'reliability KPI event-level duration reconciliation failed; possible downtime multiplication';
    END IF;

    IF (SELECT COUNT(*) FROM analytics.vw_equipment_reliability_kpi) <> 255 THEN
        RAISE EXCEPTION 'reliability KPI reliability KPI view does not cover all 255 equipment rows';
    END IF;
    IF COALESCE((SELECT SUM(corrective_failure_count)
                 FROM analytics.vw_equipment_reliability_kpi), 0)
       <> expected_failure_events
       OR COALESCE((SELECT SUM(corrective_work_order_count)
                    FROM analytics.vw_equipment_reliability_kpi), 0)
       <> expected_work_orders THEN
        RAISE EXCEPTION 'reliability KPI KPI output does not reconcile to canonical failure-event/work-order grains';
    END IF;
    IF ABS(COALESCE((SELECT SUM(linked_failure_downtime_hours)
                     FROM analytics.vw_equipment_reliability_kpi), 0)
           - expected_downtime_hours) > 0.000001
       OR ABS(COALESCE((SELECT SUM(total_corrective_repair_hours)
                        FROM analytics.vw_equipment_reliability_kpi), 0)
              - expected_repair_hours) > 0.000001 THEN
        RAISE EXCEPTION 'reliability KPI KPI duration output indicates duplicated or omitted failure/work-order measures';
    END IF;
    IF expected_failure_events <> 46670 OR expected_work_orders <> 46670 THEN
        RAISE EXCEPTION 'reliability KPI accepted source snapshot changed from 46,670 failure events / work orders';
    END IF;

    SELECT COUNT(*) INTO bad_count
    FROM analytics.vw_equipment_reliability_kpi
    WHERE mttr_hours <= 0 OR mean_calendar_inter_failure_hours <= 0
       OR operating_hours_mtbf_proxy <= 0
       OR reliability_availability_proxy < 0
       OR reliability_availability_proxy > 1;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'reliability KPI KPI sanity gate found % invalid equipment rows', bad_count;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM analytics.vw_equipment_reliability_kpi k
        LEFT JOIN dim_source_dataset s
          ON s.source_dataset_id = k.source_dataset_id
        WHERE s.source_code IS DISTINCT FROM 'SYNTHETIC_ENTERPRISE'
           OR s.is_real_data IS DISTINCT FROM FALSE
    ) THEN
        RAISE EXCEPTION 'reliability KPI provenance gate expected only synthetic Velora integration data';
    END IF;
END
$validation$;
