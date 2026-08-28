from pathlib import Path
import argparse
import psycopg

from connection_auth import connection_parameters

EXPECTED_COUNTS = {
    "dim_source_dataset": 15,
    "dim_site": 6,
    "dim_area": 12,
    "dim_line": 30,
    "dim_equipment": 255,
    "dim_sensor": 0,
    "dim_product": 6,
    "dim_shift": 3,
    "dim_failure_reason": 23,
    "dim_utility": 7,
    "dim_time": 8035,
    "fact_production": 65790,
    "fact_downtime": 170408,
    "fact_quality": 257794,
    "fact_maintenance": 46670,
    "fact_energy": 65790,
    "ref_itac_assessment": 22901,
    "ref_itac_recommendation": 169953,
    "ref_fmucd_maintenance": 3731442,
    "ref_statcan_water": 676,
    "ref_eia_mecs": 3368,
    "ref_eu_ets": 84056,
}

# The generic Eurostat reference loader intentionally loads every materialized
# Silver Parquet under Eurostat. Its exact row count therefore changes when the
# governed Silver package gains metadata or expanded observation artifacts.
MINIMUM_COUNTS = {
    "ref_eurostat_energy_price": 1,
}

def scalar(cur, sql, params=()):
    cur.execute(sql, params)
    return cur.fetchone()[0]

def check(name, actual, expected=0):
    status = "PASS" if actual == expected else "FAIL"
    print(f"{status:4s}  {name:38s} actual={actual:,} expected={expected:,}")
    return status == "PASS"


def check_at_least(name, actual, minimum):
    status = "PASS" if actual >= minimum else "FAIL"
    print(
        f"{status:4s}  {name:38s} "
        f"actual={actual:,} minimum={minimum:,}"
    )
    return status == "PASS"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5433)
    parser.add_argument("--dbname", default="manufacturing_intelligence")
    parser.add_argument("--user", default="postgres")
    args = parser.parse_args()

    ok = True

    with psycopg.connect(**connection_parameters(args)) as conn:
        with conn.cursor() as cur:
            sid = scalar(cur, "SELECT source_dataset_id FROM dim_source_dataset WHERE source_code='SYNTHETIC_ENTERPRISE'")

            print("\nRow-count validation")
            print("--------------------")
            for table, expected in EXPECTED_COUNTS.items():
                if table.startswith("fact_"):
                    actual = scalar(cur, f"SELECT COUNT(*) FROM {table} WHERE source_dataset_id=%s", (sid,))
                else:
                    actual = scalar(cur, f"SELECT COUNT(*) FROM {table}")
                ok &= check(table, actual, expected)

            for table, minimum in MINIMUM_COUNTS.items():
                actual = scalar(cur, f"SELECT COUNT(*) FROM {table}")
                ok &= check_at_least(table, actual, minimum)

            print("\nLineage validation")
            print("------------------")
            queries = {
                "downtime -> production orphans": """
                    SELECT COUNT(*) FROM fact_downtime d
                    LEFT JOIN fact_production p
                      ON p.source_dataset_id=d.source_dataset_id
                     AND p.source_record_id=d.production_record_id
                    WHERE d.source_dataset_id=%s AND p.production_id IS NULL
                """,
                "quality -> production orphans": """
                    SELECT COUNT(*) FROM fact_quality q
                    LEFT JOIN fact_production p
                      ON p.source_dataset_id=q.source_dataset_id
                     AND p.source_record_id=q.production_record_id
                    WHERE q.source_dataset_id=%s AND p.production_id IS NULL
                """,
                "maintenance -> downtime orphans": """
                    SELECT COUNT(*) FROM fact_maintenance m
                    LEFT JOIN fact_downtime d
                      ON d.source_dataset_id=m.downtime_source_dataset_id
                     AND d.source_record_id=m.downtime_event_id
                    WHERE m.source_dataset_id=%s AND d.downtime_id IS NULL
                """,
                "energy -> production orphans": """
                    SELECT COUNT(*) FROM fact_energy e
                    LEFT JOIN fact_production p
                      ON p.source_dataset_id=e.source_dataset_id
                     AND p.source_record_id=e.production_record_id
                    WHERE e.source_dataset_id=%s AND p.production_id IS NULL
                """
            }
            for name, q in queries.items():
                ok &= check(name, scalar(cur, q, (sid,)), 0)

            print("\nBusiness-rule validation")
            print("------------------------")
            rules = {
                "production quantity mismatch": """
                    SELECT COUNT(*) FROM fact_production
                    WHERE source_dataset_id=%s
                      AND actual_quantity <> good_quantity + reject_quantity
                """,
                "production invalid time": """
                    SELECT COUNT(*) FROM fact_production
                    WHERE source_dataset_id=%s
                      AND (operating_time_min < 0
                           OR planned_production_time_min < 0
                           OR operating_time_min > planned_production_time_min
                           OR timestamp_end <= timestamp_start)
                """,
                "downtime invalid duration": """
                    SELECT COUNT(*) FROM fact_downtime
                    WHERE source_dataset_id=%s
                      AND (duration_min <= 0 OR event_end <= event_start
                           OR ABS(duration_min - EXTRACT(EPOCH FROM (event_end-event_start))/60.0) > 0.001)
                """,
                "maintenance invalid interval": """
                    SELECT COUNT(*) FROM fact_maintenance
                    WHERE source_dataset_id=%s
                      AND (duration_hours <= 0 OR labor_hours < 0
                           OR end_timestamp <= start_timestamp
                           OR ABS(duration_hours - EXTRACT(EPOCH FROM (end_timestamp-start_timestamp))/3600.0) > 0.001)
                """,
                "energy invalid values": """
                    SELECT COUNT(*) FROM fact_energy
                    WHERE source_dataset_id=%s
                      AND (consumption <= 0 OR demand <= 0 OR measurement_unit <> 'kWh')
                """,
            }
            for name, q in rules.items():
                ok &= check(name, scalar(cur, q, (sid,)), 0)

    print("\nOverall database integrity validation:", "PASS" if ok else "FAIL")
    if not ok:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
