from pathlib import Path
import argparse
import csv
from datetime import date, timedelta

import psycopg

from connection_auth import connection_parameters

ROOT = Path(__file__).resolve().parents[2]

def csv_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        yield from csv.DictReader(f)

def none_if_blank(value):
    if value is None:
        return None
    value = str(value).strip()
    return None if value == "" else value

def as_bool(value):
    return str(value).strip().lower() in ("true", "1", "yes", "y")

def get_id(cur, table, id_col, where_col, value):
    cur.execute(f"SELECT {id_col} FROM {table} WHERE {where_col} = %s", (value,))
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"Missing {table}.{where_col}={value}")
    return row[0]

def load_sources(cur):
    path = ROOT / "data_model" / "source_mapping" / "source_dataset_seed.csv"
    for r in csv_rows(path):
        cur.execute(
            """
            INSERT INTO dim_source_dataset
                (source_code, source_name, publisher, source_domain, integration_role,
                 is_real_data, source_url, reference_period, notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (source_code) DO UPDATE SET
                source_name = EXCLUDED.source_name,
                publisher = EXCLUDED.publisher,
                source_domain = EXCLUDED.source_domain,
                integration_role = EXCLUDED.integration_role,
                is_real_data = EXCLUDED.is_real_data,
                source_url = EXCLUDED.source_url,
                reference_period = EXCLUDED.reference_period,
                notes = EXCLUDED.notes
            """,
            (
                r["source_code"], r["source_name"], none_if_blank(r["publisher"]),
                r["source_domain"], r["integration_role"], as_bool(r["is_real_data"]),
                none_if_blank(r["source_url"]), none_if_blank(r["reference_period"]),
                none_if_blank(r["notes"])
            )
        )

def load_sites(cur):
    synthetic_source_id = get_id(cur, "dim_source_dataset", "source_dataset_id", "source_code", "SYNTHETIC_ENTERPRISE")
    path = ROOT / "data_model" / "dimensions" / "fictional_site_registry.csv"
    for r in csv_rows(path):
        cur.execute(
            """
            INSERT INTO dim_site
                (site_code, site_name, country_code, region, site_type,
                 source_dataset_id, site_origin, active_flag)
            VALUES (%s,%s,%s,%s,%s,%s,'FICTIONAL_ENTERPRISE',TRUE)
            ON CONFLICT (site_code) DO UPDATE SET
                site_name = EXCLUDED.site_name,
                country_code = EXCLUDED.country_code,
                region = EXCLUDED.region,
                site_type = EXCLUDED.site_type,
                source_dataset_id = EXCLUDED.source_dataset_id,
                site_origin = EXCLUDED.site_origin,
                active_flag = EXCLUDED.active_flag
            """,
            (
                r["site_code"], r["site_name"], none_if_blank(r["country_code"]),
                none_if_blank(r["reference_city"]), "BEVERAGE_MANUFACTURING",
                synthetic_source_id
            )
        )

def load_areas(cur):
    path = ROOT / "data_model" / "dimensions" / "area_master.csv"
    for r in csv_rows(path):
        site_id = get_id(cur, "dim_site", "site_id", "site_code", r["site_code"])
        cur.execute(
            """
            INSERT INTO dim_area (site_id, area_code, area_name, area_type)
            VALUES (%s,%s,%s,%s)
            ON CONFLICT (site_id, area_code) DO UPDATE SET
                area_name = EXCLUDED.area_name,
                area_type = EXCLUDED.area_type
            """,
            (site_id, r["area_code"], r["area_name"], r["area_type"])
        )

def load_products(cur):
    synthetic_source_id = get_id(cur, "dim_source_dataset", "source_dataset_id", "source_code", "SYNTHETIC_ENTERPRISE")
    path = ROOT / "data_model" / "dimensions" / "product_portfolio.csv"
    for r in csv_rows(path):
        cur.execute(
            """
            INSERT INTO dim_product
                (product_code, product_name, product_family, package_type,
                 package_size, package_unit, source_dataset_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (source_dataset_id, product_code) DO UPDATE SET
                product_name = EXCLUDED.product_name,
                product_family = EXCLUDED.product_family,
                package_type = EXCLUDED.package_type,
                package_size = EXCLUDED.package_size,
                package_unit = EXCLUDED.package_unit
            """,
            (
                r["product_code"], r["product_name"], none_if_blank(r["product_family"]),
                none_if_blank(r["package_type"]), none_if_blank(r["package_size"]),
                none_if_blank(r["package_unit"]), synthetic_source_id
            )
        )

def load_shifts(cur):
    path = ROOT / "data_model" / "dimensions" / "shift_master.csv"
    for r in csv_rows(path):
        cur.execute(
            """
            INSERT INTO dim_shift
                (shift_code, shift_name, start_time, end_time, crosses_midnight)
            VALUES (%s,%s,%s,%s,%s)
            ON CONFLICT (shift_code) DO UPDATE SET
                shift_name = EXCLUDED.shift_name,
                start_time = EXCLUDED.start_time,
                end_time = EXCLUDED.end_time,
                crosses_midnight = EXCLUDED.crosses_midnight
            """,
            (r["shift_code"], r["shift_name"], r["start_time"], r["end_time"], as_bool(r["crosses_midnight"]))
        )

def load_lines(cur):
    synthetic_source_id = get_id(cur, "dim_source_dataset", "source_dataset_id", "source_code", "SYNTHETIC_ENTERPRISE")
    path = ROOT / "data_model" / "dimensions" / "line_master.csv"
    for r in csv_rows(path):
        site_id = get_id(cur, "dim_site", "site_id", "site_code", r["site_code"])
        cur.execute("SELECT area_id FROM dim_area WHERE site_id=%s AND area_code='PROD'", (site_id,))
        area_id = cur.fetchone()[0]
        cur.execute(
            """
            INSERT INTO dim_line
                (site_id, area_id, line_code, line_name, line_type,
                 nominal_capacity, capacity_unit, commissioning_year,
                 source_dataset_id, active_flag)
            VALUES (%s,%s,%s,%s,%s,%s,%s,NULL,%s,TRUE)
            ON CONFLICT (site_id, line_code) DO UPDATE SET
                area_id = EXCLUDED.area_id,
                line_name = EXCLUDED.line_name,
                line_type = EXCLUDED.line_type,
                nominal_capacity = EXCLUDED.nominal_capacity,
                capacity_unit = EXCLUDED.capacity_unit,
                source_dataset_id = EXCLUDED.source_dataset_id,
                active_flag = EXCLUDED.active_flag
            """,
            (
                site_id, area_id, r["line_code"], r["line_name"], r["line_class_code"],
                none_if_blank(r["nominal_capacity"]), none_if_blank(r["capacity_unit"]),
                synthetic_source_id
            )
        )

def load_equipment(cur):
    synthetic_source_id = get_id(cur, "dim_source_dataset", "source_dataset_id", "source_code", "SYNTHETIC_ENTERPRISE")
    path = ROOT / "data_model" / "dimensions" / "equipment_master.csv"
    for r in csv_rows(path):
        site_id = get_id(cur, "dim_site", "site_id", "site_code", r["site_code"])
        if none_if_blank(r["line_code"]):
            cur.execute("SELECT line_id FROM dim_line WHERE site_id=%s AND line_code=%s", (site_id, r["line_code"]))
            line_id = cur.fetchone()[0]
            area_code = "PROD"
        else:
            line_id = None
            area_code = "UTIL"

        cur.execute("SELECT area_id FROM dim_area WHERE site_id=%s AND area_code=%s", (site_id, area_code))
        area_id = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO dim_equipment
                (line_id, area_id, equipment_code, equipment_name, equipment_type,
                 criticality_class, commissioning_date, rated_power_kw,
                 source_dataset_id, active_flag)
            VALUES (%s,%s,%s,%s,%s,NULL,NULL,%s,%s,TRUE)
            ON CONFLICT (source_dataset_id, equipment_code) DO UPDATE SET
                line_id = EXCLUDED.line_id,
                area_id = EXCLUDED.area_id,
                equipment_name = EXCLUDED.equipment_name,
                equipment_type = EXCLUDED.equipment_type,
                rated_power_kw = EXCLUDED.rated_power_kw,
                active_flag = EXCLUDED.active_flag
            """,
            (
                line_id, area_id, r["equipment_code"], r["equipment_name"],
                r["equipment_type"], none_if_blank(r["rated_power_kw"]), synthetic_source_id
            )
        )

def load_failure_reasons(cur):
    synthetic_source_id = get_id(cur, "dim_source_dataset", "source_dataset_id", "source_code", "SYNTHETIC_ENTERPRISE")
    path = ROOT / "data_model" / "dimensions" / "failure_reason_seed.csv"
    for r in csv_rows(path):
        cur.execute(
            """
            SELECT failure_reason_id
            FROM dim_failure_reason
            WHERE failure_category=%s
              AND failure_reason=%s
              AND planned_flag=%s
              AND source_dataset_id=%s
            """,
            (r["failure_category"], r["failure_reason"], as_bool(r["planned_flag"]), synthetic_source_id)
        )
        existing = cur.fetchone()
        if existing:
            cur.execute(
                """
                UPDATE dim_failure_reason
                SET source_reason_code=%s
                WHERE failure_reason_id=%s
                """,
                (r["source_reason_code"], existing[0])
            )
        else:
            cur.execute(
                """
                INSERT INTO dim_failure_reason
                    (failure_category, failure_reason, planned_flag,
                     source_reason_code, source_dataset_id)
                VALUES (%s,%s,%s,%s,%s)
                """,
                (
                    r["failure_category"], r["failure_reason"], as_bool(r["planned_flag"]),
                    r["source_reason_code"], synthetic_source_id
                )
            )

def load_time(cur):
    d = date(2005, 1, 1)
    end = date(2026, 12, 31)
    batch = []
    while d <= end:
        iso = d.isocalendar()
        batch.append((
            int(d.strftime("%Y%m%d")), d, d.year, (d.month - 1)//3 + 1,
            d.month, d.strftime("%B"), iso.week, d.day,
            d.isoweekday(), d.strftime("%A"), d.weekday() >= 5
        ))
        d += timedelta(days=1)

    cur.executemany(
        """
        INSERT INTO dim_time
            (date_id, calendar_date, year, quarter, month, month_name,
             week_of_year, day_of_month, day_of_week, day_name, is_weekend)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (calendar_date) DO NOTHING
        """,
        batch
    )

def print_counts(cur):
    tables = [
        "dim_source_dataset","dim_site","dim_area","dim_line","dim_equipment",
        "dim_sensor","dim_product","dim_shift","dim_failure_reason","dim_utility","dim_time"
    ]
    print("\nDimension row counts")
    print("--------------------")
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"{table:22s} {cur.fetchone()[0]:,}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5433)
    parser.add_argument("--dbname", default="manufacturing_intelligence")
    parser.add_argument("--user", default="postgres")
    args = parser.parse_args()

    with psycopg.connect(**connection_parameters(args)) as conn:
        with conn.cursor() as cur:
            load_sources(cur)
            load_sites(cur)
            load_areas(cur)
            load_products(cur)
            load_shifts(cur)
            load_lines(cur)
            load_equipment(cur)
            load_failure_reasons(cur)
            load_time(cur)
            print_counts(cur)

    print("\nmaster-dimension master-dimension load complete.")

if __name__ == "__main__":
    main()
