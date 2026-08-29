from pathlib import Path
import argparse
import psycopg

from connection_auth import connection_parameters
from dq_exit_semantics import exit_code_for_statuses

CHECKS = [
("PROD_REQUIRED_NULLS","fact_production","""
SELECT COUNT(*), COUNT(*) FILTER (
WHERE timestamp_start IS NULL OR timestamp_end IS NULL OR date_id IS NULL
OR site_id IS NULL OR line_id IS NULL OR product_id IS NULL OR shift_id IS NULL
OR planned_quantity IS NULL OR actual_quantity IS NULL
OR good_quantity IS NULL OR reject_quantity IS NULL
OR operating_time_min IS NULL OR planned_production_time_min IS NULL
OR source_record_id IS NULL)
FROM fact_production WHERE source_dataset_id=%s
"""),
("PROD_DUP_SOURCE","fact_production","""
WITH x AS (
 SELECT source_record_id FROM fact_production
 WHERE source_dataset_id=%s GROUP BY source_record_id HAVING COUNT(*)>1
)
SELECT (SELECT COUNT(*) FROM fact_production WHERE source_dataset_id=%s), COUNT(*) FROM x
"""),
("PROD_QTY_RECON","fact_production","""
SELECT COUNT(*), COUNT(*) FILTER (WHERE actual_quantity<>good_quantity+reject_quantity)
FROM fact_production WHERE source_dataset_id=%s
"""),
("PROD_TIME_VALID","fact_production","""
SELECT COUNT(*), COUNT(*) FILTER (
WHERE timestamp_end<=timestamp_start OR operating_time_min<0
OR planned_production_time_min<0 OR operating_time_min>planned_production_time_min)
FROM fact_production WHERE source_dataset_id=%s
"""),

("DT_REQUIRED_NULLS","fact_downtime","""
SELECT COUNT(*), COUNT(*) FILTER (
WHERE event_start IS NULL OR event_end IS NULL OR site_id IS NULL OR line_id IS NULL
OR duration_min IS NULL OR planned_flag IS NULL
OR source_record_id IS NULL OR production_record_id IS NULL)
FROM fact_downtime WHERE source_dataset_id=%s
"""),
("DT_DUP_SOURCE","fact_downtime","""
WITH x AS (
 SELECT source_record_id FROM fact_downtime
 WHERE source_dataset_id=%s GROUP BY source_record_id HAVING COUNT(*)>1
)
SELECT (SELECT COUNT(*) FROM fact_downtime WHERE source_dataset_id=%s), COUNT(*) FROM x
"""),
("DT_DURATION_RECON","fact_downtime","""
SELECT COUNT(*), COUNT(*) FILTER (
WHERE duration_min<=0 OR event_end<=event_start
OR ABS(duration_min-EXTRACT(EPOCH FROM (event_end-event_start))/60.0)>0.001)
FROM fact_downtime WHERE source_dataset_id=%s
"""),
("DT_LINEAGE","fact_downtime","""
SELECT COUNT(*), COUNT(*) FILTER (WHERE p.production_id IS NULL)
FROM fact_downtime d
LEFT JOIN fact_production p
ON p.source_dataset_id=d.source_dataset_id AND p.source_record_id=d.production_record_id
WHERE d.source_dataset_id=%s
"""),

("QUALITY_REQUIRED_NULLS","fact_quality","""
SELECT COUNT(*), COUNT(*) FILTER (
WHERE timestamp IS NULL OR site_id IS NULL OR line_id IS NULL OR product_id IS NULL
OR reject_quantity IS NULL OR source_record_id IS NULL OR production_record_id IS NULL)
FROM fact_quality WHERE source_dataset_id=%s
"""),
("QUALITY_DUP_SOURCE","fact_quality","""
WITH x AS (
 SELECT source_record_id FROM fact_quality
 WHERE source_dataset_id=%s GROUP BY source_record_id HAVING COUNT(*)>1
)
SELECT (SELECT COUNT(*) FROM fact_quality WHERE source_dataset_id=%s), COUNT(*) FROM x
"""),
("QUALITY_LINEAGE","fact_quality","""
SELECT COUNT(*), COUNT(*) FILTER (WHERE p.production_id IS NULL)
FROM fact_quality q
LEFT JOIN fact_production p
ON p.source_dataset_id=q.source_dataset_id AND p.source_record_id=q.production_record_id
WHERE q.source_dataset_id=%s
"""),

("MAINT_REQUIRED_NULLS","fact_maintenance","""
SELECT COUNT(*), COUNT(*) FILTER (
WHERE site_id IS NULL OR equipment_id IS NULL OR work_order_id IS NULL
OR start_timestamp IS NULL OR end_timestamp IS NULL
OR duration_hours IS NULL OR labor_hours IS NULL
OR source_record_id IS NULL OR downtime_source_dataset_id IS NULL
OR downtime_event_id IS NULL)
FROM fact_maintenance WHERE source_dataset_id=%s
"""),
("MAINT_DUP_SOURCE","fact_maintenance","""
WITH x AS (
 SELECT source_record_id FROM fact_maintenance
 WHERE source_dataset_id=%s GROUP BY source_record_id HAVING COUNT(*)>1
)
SELECT (SELECT COUNT(*) FROM fact_maintenance WHERE source_dataset_id=%s), COUNT(*) FROM x
"""),
("MAINT_INTERVAL_VALID","fact_maintenance","""
SELECT COUNT(*), COUNT(*) FILTER (
WHERE duration_hours<=0 OR labor_hours<0 OR end_timestamp<=start_timestamp
OR ABS(duration_hours-EXTRACT(EPOCH FROM (end_timestamp-start_timestamp))/3600.0)>0.001)
FROM fact_maintenance WHERE source_dataset_id=%s
"""),
("MAINT_LINEAGE","fact_maintenance","""
SELECT COUNT(*), COUNT(*) FILTER (WHERE d.downtime_id IS NULL)
FROM fact_maintenance m
LEFT JOIN fact_downtime d
ON d.source_dataset_id=m.downtime_source_dataset_id
AND d.source_record_id=m.downtime_event_id
WHERE m.source_dataset_id=%s
"""),

("ENERGY_REQUIRED_NULLS","fact_energy","""
SELECT COUNT(*), COUNT(*) FILTER (
WHERE timestamp IS NULL OR site_id IS NULL OR line_id IS NULL OR utility_id IS NULL
OR consumption IS NULL OR measurement_unit IS NULL
OR source_record_id IS NULL OR production_record_id IS NULL)
FROM fact_energy WHERE source_dataset_id=%s
"""),
("ENERGY_DUP_SOURCE","fact_energy","""
WITH x AS (
 SELECT source_record_id FROM fact_energy
 WHERE source_dataset_id=%s GROUP BY source_record_id HAVING COUNT(*)>1
)
SELECT (SELECT COUNT(*) FROM fact_energy WHERE source_dataset_id=%s), COUNT(*) FROM x
"""),
("ENERGY_POSITIVE","fact_energy","""
SELECT COUNT(*), COUNT(*) FILTER (WHERE consumption<=0 OR demand<=0)
FROM fact_energy WHERE source_dataset_id=%s
"""),
("ENERGY_LINEAGE","fact_energy","""
SELECT COUNT(*), COUNT(*) FILTER (WHERE p.production_id IS NULL)
FROM fact_energy e
LEFT JOIN fact_production p
ON p.source_dataset_id=e.source_dataset_id AND p.source_record_id=e.production_record_id
WHERE e.source_dataset_id=%s
"""),

("SITE_ENERGY_RECON","fact_site_energy_detail","""
SELECT COUNT(*), COUNT(*) FILTER (
WHERE ABS(site_total_electricity_kwh-(line_electricity_kwh+site_auxiliary_electricity_kwh))>0.001)
FROM fact_site_energy_detail WHERE source_dataset_id=%s
"""),
("LINE_ENERGY_RECON","fact_line_energy_detail","""
SELECT COUNT(*), COUNT(*) FILTER (
WHERE ABS(line_total_electricity_kwh-(line_production_electricity_kwh+line_idle_electricity_kwh))>0.001)
FROM fact_line_energy_detail WHERE source_dataset_id=%s
"""),
("AUX_ENERGY_RECON","fact_site_energy_detail","""
SELECT COUNT(*), COUNT(*) FILTER (
WHERE ABS(site_auxiliary_electricity_kwh-((site_auxiliary_base_kw+site_weather_auxiliary_kw)*shift_hours))>0.001)
FROM fact_site_energy_detail WHERE source_dataset_id=%s
"""),
]

TELEMETRY_CHECKS = [
("TELEMETRY_REQUIRED_FIELDS_COMPLETE", "analytics.metropt_enterprise_telemetry", """
SELECT COUNT(*), COUNT(*) FILTER (
WHERE event_timestamp IS NULL OR source_event_timestamp IS NULL
OR site_id IS NULL OR equipment_id IS NULL OR source_dataset_id IS NULL
OR scenario_source_dataset_id IS NULL OR condition_score IS NULL
OR degradation_index IS NULL OR condition_state IS NULL
OR selected_warning_state IS NULL OR selected_warning_horizon_hours IS NULL
OR source_data_origin IS NULL OR scenario_type IS NULL
OR transformation_basis IS NULL OR degradation_signal_origin IS NULL)
FROM analytics.metropt_enterprise_telemetry
""", "FAIL", None),
("TELEMETRY_EQUIPMENT_TIMESTAMP_UNIQUE", "analytics.metropt_enterprise_telemetry", """
WITH duplicates AS (
 SELECT COUNT(*) - 1 AS duplicate_rows
 FROM analytics.metropt_enterprise_telemetry
 GROUP BY equipment_id, event_timestamp
 HAVING COUNT(*) > 1
)
SELECT
 (SELECT COUNT(*) FROM analytics.metropt_enterprise_telemetry),
 COALESCE(SUM(duplicate_rows), 0)
FROM duplicates
""", "FAIL", None),
("TELEMETRY_ENTERPRISE_MAPPING_VALID", "analytics.metropt_enterprise_telemetry", """
SELECT COUNT(*), COUNT(*) FILTER (
WHERE s.site_id IS NULL OR e.equipment_id IS NULL
OR s.site_id IS DISTINCT FROM t.site_id
OR e.equipment_type IS DISTINCT FROM 'COMPRESSED_AIR_SYSTEM')
FROM analytics.metropt_enterprise_telemetry t
LEFT JOIN dim_equipment e ON e.equipment_id = t.equipment_id
LEFT JOIN dim_area a ON a.area_id = e.area_id
LEFT JOIN dim_site s ON s.site_id = a.site_id
""", "FAIL", None),
("TELEMETRY_LINEAGE_VALID", "analytics.metropt_enterprise_telemetry", """
SELECT COUNT(*), COUNT(*) FILTER (
WHERE t.source_data_origin IS DISTINCT FROM 'EXTERNAL_REAL'
OR t.scenario_type IS DISTINCT FROM 'SYNTHETIC_ENTERPRISE_ADAPTATION'
OR t.transformation_basis IS DISTINCT FROM 'METROPT_INFORMED'
OR t.degradation_signal_origin IS DISTINCT FROM 'SYNTHETIC_CONTROLLED'
OR src.source_code IS DISTINCT FROM 'METROPT3'
OR scenario.source_code IS DISTINCT FROM 'METROPT3_ENTERPRISE_PDM'
OR t.source_event_timestamp >= t.event_timestamp)
FROM analytics.metropt_enterprise_telemetry t
LEFT JOIN dim_source_dataset src
  ON src.source_dataset_id = t.source_dataset_id
LEFT JOIN dim_source_dataset scenario
  ON scenario.source_dataset_id = t.scenario_source_dataset_id
""", "FAIL", None),
("TELEMETRY_CADENCE_CONTINUITY", "analytics.metropt_enterprise_telemetry", """
WITH intervals AS (
 SELECT event_timestamp - LAG(event_timestamp) OVER (
   PARTITION BY equipment_id ORDER BY event_timestamp
 ) AS observed_interval
 FROM analytics.metropt_enterprise_telemetry
)
SELECT COUNT(*), COUNT(*) FILTER (WHERE observed_interval <> INTERVAL '5 minutes')
FROM intervals
WHERE observed_interval IS NOT NULL
""", "WARN",
 "Non-five-minute intervals quantify retained source availability and non-operating gaps; physical fault and warning states are not DQ defects."),
]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--host",default="localhost")
    ap.add_argument("--port",type=int,default=5433)
    ap.add_argument("--dbname",default="manufacturing_intelligence")
    ap.add_argument("--user",default="postgres")
    args=ap.parse_args()
    result_statuses = []

    with psycopg.connect(**connection_parameters(args)) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT source_dataset_id FROM dim_source_dataset WHERE source_code='SYNTHETIC_ENTERPRISE'")
            syn=cur.fetchone()[0]
            cur.execute("SELECT source_dataset_id FROM dim_source_dataset WHERE source_code='EUROSTAT_ENERGY_PRICES'")
            eur=cur.fetchone()[0]
            cur.execute("SELECT source_dataset_id FROM dim_source_dataset WHERE source_code='METROPT3_ENTERPRISE_PDM'")
            telemetry_source=cur.fetchone()[0]

            cur.execute("DELETE FROM dq_result")
            print("Running data-quality rules...\n")

            for code,obj,q in CHECKS:
                params=(syn,syn) if q.count("%s")==2 else (syn,)
                cur.execute(q,params)
                evaluated,failed=cur.fetchone()
                cur.execute("SELECT dq_rule_id FROM dq_rule WHERE rule_code=%s",(code,))
                rule_id=cur.fetchone()[0]
                rate=(failed/evaluated) if evaluated else 0
                status="PASS" if failed==0 else "FAIL"
                result_statuses.append(status)
                cur.execute("""
                    INSERT INTO dq_result
                    (dq_rule_id,source_dataset_id,target_object,evaluated_row_count,
                     failed_row_count,failure_rate,result_status,result_detail)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """,(rule_id,syn,obj,evaluated,failed,rate,status,None))
                print(f"{status:4s} {code:28s} evaluated={evaluated:,} failed={failed:,}")

            # Eurostat coverage
            cur.execute("""
                SELECT COUNT(*) FROM ref_eurostat_electricity_price_observation
                WHERE dataset_code='nrg_pc_205'
                  AND consumption_band_code='MWH2000-19999'
                  AND tax_code='X_VAT'
                  AND currency_code='EUR'
                  AND unit_code='KWH'
            """)
            n=cur.fetchone()[0]
            failed=0 if n==24 else abs(24-n)
            for code,failed_count,detail in [
                ("EUROSTAT_PRICE_COVERAGE",failed,f"Expected 24 selected rows; found {n}."),
            ]:
                status = "PASS" if failed_count == 0 else "FAIL"
                result_statuses.append(status)
                cur.execute("SELECT dq_rule_id FROM dq_rule WHERE rule_code=%s",(code,))
                rid=cur.fetchone()[0]
                cur.execute("""
                    INSERT INTO dq_result
                    (dq_rule_id,source_dataset_id,target_object,evaluated_row_count,
                     failed_row_count,failure_rate,result_status,result_detail)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """,(rid,eur,"ref_eurostat_electricity_price_observation",24,failed_count,
                     failed_count/24 if 24 else 0,status,detail))
                print(f"{status:4s} {code:28s} evaluated=24 failed={failed_count}")

            cur.execute("""
                SELECT COUNT(*),
                       COUNT(*) FILTER (WHERE price_value<=0)
                FROM ref_eurostat_electricity_price_observation
                WHERE dataset_code='nrg_pc_205'
                  AND consumption_band_code='MWH2000-19999'
                  AND tax_code='X_VAT'
                  AND currency_code='EUR'
                  AND unit_code='KWH'
            """)
            evaluated,failed=cur.fetchone()
            status = "PASS" if failed == 0 else "FAIL"
            result_statuses.append(status)
            cur.execute("SELECT dq_rule_id FROM dq_rule WHERE rule_code='EUROSTAT_PRICE_POSITIVE'")
            rid=cur.fetchone()[0]
            cur.execute("""
                INSERT INTO dq_result
                (dq_rule_id,source_dataset_id,target_object,evaluated_row_count,
                 failed_row_count,failure_rate,result_status,result_detail)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """,(rid,eur,"ref_eurostat_electricity_price_observation",evaluated,failed,
                 failed/evaluated if evaluated else 0,status,None))
            print(f"{status:4s} {'EUROSTAT_PRICE_POSITIVE':28s} evaluated={evaluated:,} failed={failed:,}")

            for code, obj, query, failure_status, detail in TELEMETRY_CHECKS:
                cur.execute(query)
                evaluated, failed = cur.fetchone()
                cur.execute("SELECT dq_rule_id FROM dq_rule WHERE rule_code=%s", (code,))
                rule_id = cur.fetchone()[0]
                rate = (failed / evaluated) if evaluated else 0
                status = "PASS" if failed == 0 else failure_status
                result_statuses.append(status)
                result_detail = detail if failed else None
                cur.execute("""
                    INSERT INTO dq_result
                    (dq_rule_id,source_dataset_id,target_object,evaluated_row_count,
                     failed_row_count,failure_rate,result_status,result_detail)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (rule_id, telemetry_source, obj, evaluated, failed, rate,
                      status, result_detail))
                print(f"{status:4s} {code:38s} evaluated={evaluated:,} failed={failed:,}")

            fail_rules = result_statuses.count("FAIL")
            print(f"\nFailed rules: {fail_rules}")
            print("Overall data-quality DQ result:", "PASS" if fail_rules==0 else "FAIL")

    raise SystemExit(exit_code_for_statuses(result_statuses))

if __name__=="__main__":
    main()
