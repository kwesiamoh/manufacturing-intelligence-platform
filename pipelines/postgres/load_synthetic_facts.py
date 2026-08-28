from pathlib import Path
import argparse
import math

import pandas as pd
import psycopg

from connection_auth import connection_parameters

ROOT = Path(__file__).resolve().parents[2]

PROD_PATH = ROOT / "data" / "silver" / "synthetic_enterprise" / "production" / "production_operations_2024_2025.parquet"
DT_PATH = ROOT / "data" / "silver" / "synthetic_enterprise" / "downtime" / "downtime_events_2024_2025.parquet"
QLT_PATH = ROOT / "data" / "silver" / "synthetic_enterprise" / "quality" / "quality_events_2024_2025.parquet"
MNT_PATH = ROOT / "data" / "silver" / "synthetic_enterprise" / "maintenance" / "maintenance_work_orders_2024_2025.parquet"
ENE_PATH = ROOT / "data" / "silver" / "synthetic_enterprise" / "energy" / "line_energy_utility_2024_2025.parquet"

def null(v):
    if pd.isna(v):
        return None
    return v

def naive_ts(v):
    if pd.isna(v):
        return None
    t = pd.Timestamp(v)
    if t.tzinfo is not None:
        t = t.tz_convert("UTC").tz_localize(None)
    return t.to_pydatetime()

def maps(cur):
    def simple(table, key_col, id_col):
        cur.execute(f"SELECT {key_col}, {id_col} FROM {table}")
        return dict(cur.fetchall())

    cur.execute("""
        SELECT line_code, line_id, site_id
        FROM dim_line
    """)
    line_rows = cur.fetchall()
    line_id = {r[0]: r[1] for r in line_rows}
    line_site_id = {r[0]: r[2] for r in line_rows}

    cur.execute("SELECT site_code, site_id FROM dim_site")
    site_id = dict(cur.fetchall())

    cur.execute("SELECT product_code, product_id FROM dim_product")
    product_id = dict(cur.fetchall())

    cur.execute("SELECT shift_code, shift_id FROM dim_shift")
    shift_id = dict(cur.fetchall())

    cur.execute("SELECT equipment_code, equipment_id FROM dim_equipment")
    equipment_id = dict(cur.fetchall())

    cur.execute("SELECT utility_code, utility_id FROM dim_utility")
    utility_id = dict(cur.fetchall())

    cur.execute("SELECT source_code, source_dataset_id FROM dim_source_dataset")
    source_id = dict(cur.fetchall())

    cur.execute("""
        SELECT failure_category, failure_reason, planned_flag, failure_reason_id
        FROM dim_failure_reason
    """)
    failure_id = {(r[0], r[1], r[2]): r[3] for r in cur.fetchall()}

    return {
        "site": site_id,
        "line": line_id,
        "line_site": line_site_id,
        "product": product_id,
        "shift": shift_id,
        "equipment": equipment_id,
        "utility": utility_id,
        "source": source_id,
        "failure": failure_id,
    }

def date_id(ts):
    t = pd.Timestamp(ts)
    return int(t.strftime("%Y%m%d"))

def clear_synthetic(cur, source_id):
    # Reload-safe for this synthetic source.
    for table in [
        "fact_maintenance",
        "fact_quality",
        "fact_downtime",
        "fact_energy",
        "fact_production",
    ]:
        cur.execute(f"DELETE FROM {table} WHERE source_dataset_id = %s", (source_id,))

def load_production(cur, m, source_id):
    df = pd.read_parquet(PROD_PATH)
    sql = """
        INSERT INTO fact_production (
            timestamp_start, timestamp_end, date_id, site_id, line_id,
            product_id, shift_id, source_dataset_id, planned_quantity,
            actual_quantity, good_quantity, reject_quantity, nominal_rate,
            actual_rate, operating_time_min, planned_production_time_min,
            source_record_id
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    rows = []
    for r in df.itertuples(index=False):
        actual_rate = None
        if float(r.operating_time_min) > 0:
            actual_rate = float(r.actual_quantity) / (float(r.operating_time_min) / 60.0)
        rows.append((
            naive_ts(r.timestamp_start), naive_ts(r.timestamp_end), date_id(r.timestamp_start),
            m["site"][r.site_code], m["line"][r.line_code], m["product"][r.product_code],
            m["shift"][r.shift_code], source_id,
            int(r.planned_quantity), int(r.actual_quantity), int(r.good_quantity),
            int(r.reject_quantity), float(r.nominal_rate), actual_rate,
            float(r.operating_time_min), float(r.planned_production_time_min),
            r.production_record_id
        ))
    cur.executemany(sql, rows)
    return len(rows)

def load_downtime(cur, m, source_id):
    df = pd.read_parquet(DT_PATH)
    sql = """
        INSERT INTO fact_downtime (
            event_start, event_end, date_id, site_id, line_id, equipment_id,
            shift_id, failure_reason_id, source_dataset_id, duration_min,
            planned_flag, production_loss_quantity, source_event_code,
            source_record_id, production_record_id
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    rows = []
    for r in df.itertuples(index=False):
        fid = m["failure"][(r.failure_category, r.failure_reason, bool(r.planned_flag))]
        rows.append((
            naive_ts(r.event_start), naive_ts(r.event_end), date_id(r.event_start),
            m["site"][r.site_code], m["line"][r.line_code],
            m["equipment"][r.equipment_code], m["shift"][r.shift_code],
            fid, source_id, float(r.duration_min), bool(r.planned_flag),
            None, r.source_event_code, r.downtime_event_id, r.production_record_id
        ))
    cur.executemany(sql, rows)
    return len(rows)

def load_quality(cur, m, source_id):
    df = pd.read_parquet(QLT_PATH)
    sql = """
        INSERT INTO fact_quality (
            timestamp, date_id, site_id, line_id, equipment_id, product_id,
            source_dataset_id, total_quantity, good_quantity, reject_quantity,
            rework_quantity, quality_result, defect_code, measurement_value,
            lower_spec_limit, upper_spec_limit, source_record_id,
            production_record_id
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    rows = []
    for r in df.itertuples(index=False):
        rows.append((
            naive_ts(r.event_timestamp), date_id(r.event_timestamp),
            m["site"][r.site_code], m["line"][r.line_code],
            m["equipment"][r.equipment_code], m["product"][r.product_code],
            source_id, None, None, int(r.rejected_units), int(r.rework_units),
            r.quality_result, r.defect_code, None, None, None,
            r.quality_event_id, r.production_record_id
        ))
    cur.executemany(sql, rows)
    return len(rows)

def load_maintenance(cur, m, source_id):
    df = pd.read_parquet(MNT_PATH)
    sql = """
        INSERT INTO fact_maintenance (
            site_id, equipment_id, source_dataset_id, work_order_id,
            maintenance_type, failure_reason_id, start_timestamp, end_timestamp,
            duration_hours, labor_hours, labor_cost, material_cost, other_cost,
            total_cost, planned_flag, source_record_id,
            downtime_source_dataset_id, downtime_event_id, production_record_id
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    rows = []
    for r in df.itertuples(index=False):
        fid = m["failure"][(r.failure_category, r.failure_reason, False)]
        rows.append((
            m["site"][r.site_code], m["equipment"][r.equipment_code], source_id,
            r.maintenance_id, r.maintenance_type, fid,
            naive_ts(r.start_timestamp), naive_ts(r.end_timestamp),
            float(r.duration_hours), float(r.labor_hours),
            None, None, None, None, False,
            r.maintenance_id, source_id, r.downtime_event_id,
            r.production_record_id
        ))
    cur.executemany(sql, rows)
    return len(rows)

def load_energy(cur, m, source_id):
    df = pd.read_parquet(ENE_PATH)
    elec_id = m["utility"]["ELECTRICITY"]
    sql = """
        INSERT INTO fact_energy (
            timestamp, date_id, site_id, area_id, line_id, equipment_id,
            utility_id, source_dataset_id, consumption, demand, energy_cost,
            measurement_unit, source_record_id, production_record_id
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    rows = []
    # Production-area IDs by site
    cur.execute("""
        SELECT s.site_code, a.area_id
        FROM dim_area a
        JOIN dim_site s ON s.site_id = a.site_id
        WHERE a.area_code = 'PROD'
    """)
    prod_area = dict(cur.fetchall())

    for r in df.itertuples(index=False):
        # Demand is average kW over the 8-hour shift.
        start = pd.Timestamp(r.timestamp_start)
        end = pd.Timestamp(r.timestamp_end)
        hours = (end - start).total_seconds() / 3600.0
        consumption = float(r.line_total_electricity_kwh)
        demand = consumption / hours if hours > 0 else None
        rows.append((
            naive_ts(r.timestamp_start), date_id(r.timestamp_start),
            m["site"][r.site_code], prod_area[r.site_code], m["line"][r.line_code],
            None, elec_id, source_id, consumption, demand, None, "kWh",
            r.energy_record_id, r.production_record_id
        ))
    cur.executemany(sql, rows)
    return len(rows)

def validate(cur, source_id):
    expected = {
        "fact_production": 65790,
        "fact_downtime": 170408,
        "fact_quality": 257794,
        "fact_maintenance": 46670,
        "fact_energy": 65790,
    }

    print("\nFact row counts")
    print("---------------")
    for table, exp in expected.items():
        cur.execute(f"SELECT COUNT(*) FROM {table} WHERE source_dataset_id=%s", (source_id,))
        n = cur.fetchone()[0]
        print(f"{table:20s} {n:,}  expected {exp:,}")
        if n != exp:
            raise RuntimeError(f"{table} row count mismatch: got {n}, expected {exp}")

    # Cross-fact lineage checks
    cur.execute("""
        SELECT COUNT(*)
        FROM fact_downtime d
        LEFT JOIN fact_production p
          ON p.source_dataset_id=d.source_dataset_id
         AND p.source_record_id=d.production_record_id
        WHERE d.source_dataset_id=%s
          AND p.production_id IS NULL
    """, (source_id,))
    orphan_dt = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM fact_quality q
        LEFT JOIN fact_production p
          ON p.source_dataset_id=q.source_dataset_id
         AND p.source_record_id=q.production_record_id
        WHERE q.source_dataset_id=%s
          AND p.production_id IS NULL
    """, (source_id,))
    orphan_q = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM fact_maintenance m
        LEFT JOIN fact_downtime d
          ON d.source_dataset_id=m.downtime_source_dataset_id
         AND d.source_record_id=m.downtime_event_id
        WHERE m.source_dataset_id=%s
          AND d.downtime_id IS NULL
    """, (source_id,))
    orphan_m = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM fact_energy e
        LEFT JOIN fact_production p
          ON p.source_dataset_id=e.source_dataset_id
         AND p.source_record_id=e.production_record_id
        WHERE e.source_dataset_id=%s
          AND p.production_id IS NULL
    """, (source_id,))
    orphan_e = cur.fetchone()[0]

    print("\nLineage validation")
    print("------------------")
    print(f"Downtime -> production orphans:   {orphan_dt}")
    print(f"Quality -> production orphans:    {orphan_q}")
    print(f"Maintenance -> downtime orphans:  {orphan_m}")
    print(f"Energy -> production orphans:     {orphan_e}")

    if any([orphan_dt, orphan_q, orphan_m, orphan_e]):
        raise RuntimeError("Cross-fact lineage validation failed.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5433)
    parser.add_argument("--dbname", default="manufacturing_intelligence")
    parser.add_argument("--user", default="postgres")
    args = parser.parse_args()

    for p in [PROD_PATH, DT_PATH, QLT_PATH, MNT_PATH, ENE_PATH]:
        if not p.exists():
            raise FileNotFoundError(f"Required Silver file not found: {p}")

    with psycopg.connect(**connection_parameters(args)) as conn:
        with conn.cursor() as cur:
            m = maps(cur)
            source_id = m["source"]["SYNTHETIC_ENTERPRISE"]

            clear_synthetic(cur, source_id)

            print("Loading fact_production ...")
            print(f"  {load_production(cur, m, source_id):,} rows")

            print("Loading fact_downtime ...")
            print(f"  {load_downtime(cur, m, source_id):,} rows")

            print("Loading fact_quality ...")
            print(f"  {load_quality(cur, m, source_id):,} rows")

            print("Loading fact_maintenance ...")
            print(f"  {load_maintenance(cur, m, source_id):,} rows")

            print("Loading fact_energy ...")
            print(f"  {load_energy(cur, m, source_id):,} rows")

            validate(cur, source_id)

    print("\nStage 4D/4E synthetic fact load complete.")

if __name__ == "__main__":
    main()
