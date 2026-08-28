from pathlib import Path
import argparse
import hashlib
import pandas as pd
import psycopg

from connection_auth import connection_parameters

ROOT = Path(__file__).resolve().parents[2]

LINE_PATH = ROOT / "data" / "silver" / "synthetic_enterprise" / "energy" / "line_energy_utility_2024_2025.parquet"
SITE_PATH = ROOT / "data" / "silver" / "synthetic_enterprise" / "energy" / "site_energy_2024_2025.parquet"

def naive_ts(v):
    t = pd.Timestamp(v)
    if t.tzinfo is not None:
        t = t.tz_convert("UTC").tz_localize(None)
    return t.to_pydatetime(warn=False)

def null(v):
    return None if pd.isna(v) else v

def get_map(cur, table, code_col, id_col):
    cur.execute(f"SELECT {code_col}, {id_col} FROM {table}")
    return dict(cur.fetchall())

def get_source_id(cur):
    cur.execute("SELECT source_dataset_id FROM dim_source_dataset WHERE source_code='SYNTHETIC_ENTERPRISE'")
    row = cur.fetchone()
    if not row:
        raise RuntimeError("Missing SYNTHETIC_ENTERPRISE source.")
    return row[0]

def site_record_id(row):
    raw = f"{row.site_code}|{row.shift_code}|{pd.Timestamp(row.timestamp_start).isoformat()}"
    return "SITEENERGY-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:24]

def load_line(cur, sid, maps):
    df = pd.read_parquet(LINE_PATH)

    cur.execute("DELETE FROM fact_line_energy_detail WHERE source_dataset_id=%s", (sid,))

    sql = """
        INSERT INTO fact_line_energy_detail (
            source_dataset_id, energy_record_id, production_record_id,
            site_id, line_id, shift_id, product_id,
            timestamp_start, timestamp_end, actual_quantity,
            line_production_electricity_kwh, line_idle_electricity_kwh,
            line_total_electricity_kwh, compressed_air_nm3,
            compressed_air_nm3_per_1000_units, shift_mean_air_temperature_c,
            site_auxiliary_base_kw, site_weather_auxiliary_kw,
            data_class, integration_role, weather_data_class, generator_seed
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    batch = []
    for r in df.itertuples(index=False):
        batch.append((
            sid, r.energy_record_id, r.production_record_id,
            maps["site"][r.site_code], maps["line"][r.line_code],
            maps["shift"][r.shift_code], maps["product"][r.product_code],
            naive_ts(r.timestamp_start), naive_ts(r.timestamp_end),
            int(r.actual_quantity),
            float(r.line_production_electricity_kwh),
            float(r.line_idle_electricity_kwh),
            float(r.line_total_electricity_kwh),
            null(r.compressed_air_nm3),
            null(r.compressed_air_nm3_per_1000_units),
            null(r.shift_mean_air_temperature_c),
            null(r.site_auxiliary_base_kw),
            null(r.site_weather_auxiliary_kw),
            r.data_class, r.integration_role, r.weather_data_class,
            int(r.generator_seed)
        ))
        if len(batch) >= 5000:
            cur.executemany(sql, batch)
            batch.clear()
    if batch:
        cur.executemany(sql, batch)
    return len(df)

def load_site(cur, sid, maps):
    df = pd.read_parquet(SITE_PATH)

    cur.execute("DELETE FROM fact_site_energy_detail WHERE source_dataset_id=%s", (sid,))

    sql = """
        INSERT INTO fact_site_energy_detail (
            source_dataset_id, site_energy_record_id, site_id, shift_id,
            timestamp_start, timestamp_end, line_electricity_kwh,
            production_units, mean_air_temperature_c, site_auxiliary_base_kw,
            site_weather_auxiliary_kw, shift_hours,
            site_auxiliary_electricity_kwh, site_total_electricity_kwh,
            site_energy_intensity_kwh_per_1000_units,
            data_class, integration_role, weather_data_class
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    batch = []
    for r in df.itertuples(index=False):
        batch.append((
            sid, site_record_id(r), maps["site"][r.site_code],
            maps["shift"][r.shift_code], naive_ts(r.timestamp_start),
            naive_ts(r.timestamp_end), float(r.line_electricity_kwh),
            int(r.production_units), null(r.mean_air_temperature_c),
            float(r.site_auxiliary_base_kw),
            float(r.site_weather_auxiliary_kw),
            float(r.shift_hours),
            float(r.site_auxiliary_electricity_kwh),
            float(r.site_total_electricity_kwh),
            float(r.site_energy_intensity_kwh_per_1000_units),
            r.data_class, r.integration_role, r.weather_data_class
        ))
        if len(batch) >= 5000:
            cur.executemany(sql, batch)
            batch.clear()
    if batch:
        cur.executemany(sql, batch)
    return len(df)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5433)
    parser.add_argument("--dbname", default="manufacturing_intelligence")
    parser.add_argument("--user", default="postgres")
    args = parser.parse_args()

    if not LINE_PATH.exists():
        raise FileNotFoundError(LINE_PATH)
    if not SITE_PATH.exists():
        raise FileNotFoundError(SITE_PATH)

    with psycopg.connect(**connection_parameters(args)) as conn:
        with conn.cursor() as cur:
            sid = get_source_id(cur)
            maps = {
                "site": get_map(cur, "dim_site", "site_code", "site_id"),
                "line": get_map(cur, "dim_line", "line_code", "line_id"),
                "shift": get_map(cur, "dim_shift", "shift_code", "shift_id"),
                "product": get_map(cur, "dim_product", "product_code", "product_id"),
            }

            print("Loading line energy detail ...")
            print(f"  {load_line(cur, sid, maps):,} rows")

            print("Loading site energy detail ...")
            print(f"  {load_site(cur, sid, maps):,} rows")

    print("\nStage 6B energy-detail load complete.")

if __name__ == "__main__":
    main()
