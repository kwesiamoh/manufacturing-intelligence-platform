-- failure/downtime validation
\pset pager off

\echo '=== 1. Failure-reason summary reconciliation ==='
SELECT
    SUM(downtime_event_count) AS all_downtime_events,
    SUM(unplanned_downtime_event_count) AS unplanned_downtime_events,
    SUM(corrective_linked_failure_count) AS corrective_linked_failures,
    ROUND(SUM(total_downtime_min)::numeric,2) AS total_downtime_min,
    ROUND(SUM(unplanned_downtime_min)::numeric,2) AS unplanned_downtime_min,
    ROUND(SUM(corrective_linked_downtime_min)::numeric,2)
        AS corrective_linked_downtime_min
FROM analytics.vw_failure_reason_downtime_summary;

\echo ''
\echo '=== 2. Pareto sanity ==='
SELECT
    COUNT(*) FILTER (
        WHERE unplanned_downtime_share < 0
           OR unplanned_downtime_share > 1
    ) AS invalid_share,
    COUNT(*) FILTER (
        WHERE cumulative_unplanned_downtime_share < 0
           OR cumulative_unplanned_downtime_share > 1.0000001
    ) AS invalid_cumulative_share
FROM analytics.vw_failure_reason_downtime_summary;

\echo ''
\echo '=== 3. Enterprise unplanned downtime by failure reason ==='
SELECT
    failure_category,
    failure_reason,
    SUM(unplanned_downtime_event_count) AS unplanned_events,
    SUM(corrective_linked_failure_count) AS corrective_linked_failures,
    ROUND(SUM(unplanned_downtime_min)::numeric,2) AS unplanned_downtime_min,
    ROUND(SUM(unplanned_production_loss_quantity)::numeric,0)
        AS production_loss_quantity
FROM analytics.vw_failure_reason_downtime_summary
GROUP BY failure_category, failure_reason
ORDER BY SUM(unplanned_downtime_min) DESC NULLS LAST;

\echo ''
\echo '=== 4. Top equipment by corrective downtime burden ==='
SELECT
    enterprise_downtime_burden_rank,
    site_code,
    line_code,
    equipment_code,
    equipment_type,
    corrective_failure_count,
    ROUND(linked_failure_downtime_hours::numeric,2) AS downtime_h,
    ROUND(mttr_hours::numeric,4) AS mttr_h,
    ROUND(operating_hours_mtbf_proxy::numeric,2) AS mtbf_proxy_h,
    ROUND(total_corrective_maintenance_cost::numeric,2) AS corrective_cost,
    ROUND(linked_production_loss_quantity::numeric,0) AS production_loss
FROM analytics.vw_equipment_failure_burden
ORDER BY enterprise_downtime_burden_rank
LIMIT 20;

\echo ''
\echo '=== 5. Site failure burden ==='
SELECT
    site_code,
    SUM(corrective_failure_count) AS corrective_failures,
    ROUND(SUM(linked_failure_downtime_hours)::numeric,2) AS corrective_downtime_h,
    ROUND(SUM(total_corrective_maintenance_cost)::numeric,2) AS corrective_cost,
    ROUND(SUM(linked_production_loss_quantity)::numeric,0) AS production_loss
FROM analytics.vw_equipment_failure_burden
GROUP BY site_code
ORDER BY corrective_downtime_h DESC;

\echo ''
\echo '=== failure/downtime validation complete ==='

\echo '=== Mandatory failure/downtime gate ==='
DO $validation$
DECLARE
    bad_count bigint;
    expected_downtime_events bigint;
    expected_failure_events bigint;
    expected_corrective_downtime_min numeric;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM analytics.vw_failure_reason_downtime_summary)
       OR NOT EXISTS (SELECT 1 FROM analytics.vw_equipment_failure_burden) THEN
        RAISE EXCEPTION 'failure/downtime accepted views are empty';
    END IF;

    SELECT COUNT(*) INTO expected_downtime_events
    FROM public.fact_downtime;
    SELECT
        COUNT(*),
        COALESCE(SUM(failure_downtime_hours) * 60.0, 0)
    INTO expected_failure_events, expected_corrective_downtime_min
    FROM analytics.vw_corrective_failure_event;

    IF COALESCE((SELECT SUM(downtime_event_count)
                 FROM analytics.vw_failure_reason_downtime_summary), 0)
       <> expected_downtime_events
       OR COALESCE((SELECT SUM(corrective_linked_failure_count)
                    FROM analytics.vw_failure_reason_downtime_summary), 0)
       <> expected_failure_events THEN
        RAISE EXCEPTION 'failure/downtime event populations do not reconcile at downtime/failure-event grain';
    END IF;
    IF ABS(COALESCE((SELECT SUM(corrective_linked_downtime_min)
                     FROM analytics.vw_failure_reason_downtime_summary), 0)
           - expected_corrective_downtime_min) > 0.000001 THEN
        RAISE EXCEPTION 'failure/downtime corrective downtime was multiplied or omitted';
    END IF;
    IF expected_downtime_events <> 170408
       OR expected_failure_events <> 46670 THEN
        RAISE EXCEPTION 'failure/downtime accepted source snapshot changed from 170,408 downtime / 46,670 corrective failure events';
    END IF;

    SELECT COUNT(*) INTO bad_count
    FROM analytics.vw_failure_reason_downtime_summary
    WHERE unplanned_downtime_share < 0 OR unplanned_downtime_share > 1
       OR cumulative_unplanned_downtime_share < 0
       OR cumulative_unplanned_downtime_share > 1.0000001;
    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'failure/downtime Pareto gate found % invalid rows', bad_count;
    END IF;

    IF COALESCE((SELECT SUM(corrective_failure_count)
                 FROM analytics.vw_equipment_failure_burden), 0)
       <> expected_failure_events
       OR ABS(COALESCE((SELECT SUM(linked_failure_downtime_hours)
                        FROM analytics.vw_equipment_failure_burden), 0)
              - expected_corrective_downtime_min / 60.0) > 0.000001 THEN
        RAISE EXCEPTION 'failure/downtime equipment burden does not reconcile to canonical failure-event count and downtime';
    END IF;
END
$validation$;
