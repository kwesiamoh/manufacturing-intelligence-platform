from pathlib import Path
import argparse
import json
import pandas as pd
import psycopg

from connection_auth import connection_parameters

ROOT = Path(__file__).resolve().parents[2]


def source_id(cur, code):
    cur.execute(
        "SELECT source_dataset_id FROM dim_source_dataset WHERE source_code=%s", (code,))
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"Missing dim_source_dataset source_code={code}")
    return row[0]


def to_jsonable_dict(row):
    out = {}
    for k, v in row.items():
        if pd.isna(v):
            out[k] = None
        elif isinstance(v, pd.Timestamp):
            out[k] = v.isoformat()
        else:
            out[k] = v.item() if hasattr(v, "item") else v
    return out


def insert_json_rows(cur, table, sid, df, extra_cols=None, batch_size=5000):
    extra_cols = extra_cols or {}
    cols = ["source_dataset_id"] + \
        list(extra_cols.keys()) + ["source_row_json"]
    placeholders = ",".join(["%s"] * len(cols))
    sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"

    batch = []
    for _, row in df.iterrows():
        payload = [sid] + list(extra_cols.values()) + \
            [json.dumps(to_jsonable_dict(row.to_dict()), ensure_ascii=False)]
        batch.append(tuple(payload))
        if len(batch) >= batch_size:
            cur.executemany(sql, batch)
            batch.clear()
    if batch:
        cur.executemany(sql, batch)


def first_existing(paths):
    for p in paths:
        if p.exists():
            return p
    return None


def load_itac(cur):
    sid = source_id(cur, "ITAC")
    base = ROOT / "sources" / "step08-energy-cost" / "silver" / "itac"

    assess_files = list(base.glob("*__assess.parquet"))
    recc_files = list(base.glob("*__recc.parquet"))

    if not assess_files or not recc_files:
        raise FileNotFoundError(
            "Could not locate ITAC Silver ASSESS/RECC parquet files.")

    assess = assess_files[0]
    recc = recc_files[0]

    cur.execute(
        "DELETE FROM ref_itac_assessment WHERE source_dataset_id=%s", (sid,))
    cur.execute(
        "DELETE FROM ref_itac_recommendation WHERE source_dataset_id=%s", (sid,))

    da = pd.read_parquet(assess)
    dr = pd.read_parquet(recc)

    insert_json_rows(cur, "ref_itac_assessment", sid, da)
    insert_json_rows(cur, "ref_itac_recommendation", sid, dr)

    return len(da), len(dr)


def load_fmucd(cur):
    sid = source_id(cur, "FMUCD")
    base = ROOT / "sources" / "step06-maintenance"
    p = first_existing([
        base / "silver" / "fmucd_maintenance.parquet",
        base / "data" / "silver" / "fmucd_maintenance.parquet",
    ])
    if not p:
        raise FileNotFoundError("Could not locate FMUCD Silver parquet.")
    cur.execute(
        "DELETE FROM ref_fmucd_maintenance WHERE source_dataset_id=%s", (sid,))
    df = pd.read_parquet(p)
    insert_json_rows(cur, "ref_fmucd_maintenance", sid, df)
    return len(df)


def load_statcan(cur):
    sid = source_id(cur, "STATCAN_WATER")
    base = ROOT / "sources" / "step10-water"
    p = first_existing([
        base / "silver" / "statcan_industrial_water" / "38100056.parquet",
        base / "data" / "silver" / "statcan_industrial_water" / "38100056.parquet",
    ])
    if not p:
        raise FileNotFoundError(
            "Could not locate StatCan water Silver parquet.")
    cur.execute(
        "DELETE FROM ref_statcan_water WHERE source_dataset_id=%s", (sid,))
    df = pd.read_parquet(p)
    insert_json_rows(cur, "ref_statcan_water", sid, df)
    return len(df)


def load_mecs(cur):
    sid = source_id(cur, "EIA_MECS")
    base = ROOT / "sources" / "step11-fuels"
    silver_candidates = [
        base / "silver",
        base / "data" / "silver",
    ]
    silver_root = next((p for p in silver_candidates if p.exists()), None)
    if silver_root is None:
        raise FileNotFoundError("Could not locate EIA MECS Silver folder.")

    cur.execute("DELETE FROM ref_eia_mecs WHERE source_dataset_id=%s", (sid,))
    count = 0
    files = sorted(silver_root.rglob("*.parquet"))
    if not files:
        raise FileNotFoundError("No EIA MECS parquet files found.")
    for p in files:
        df = pd.read_parquet(p)
        source_table = p.parent.name
        source_sheet = p.stem
        insert_json_rows(cur, "ref_eia_mecs", sid, df, {
            "source_table": source_table,
            "source_sheet": source_sheet
        })
        count += len(df)
    return count, len(files)


def load_euets(cur):
    sid = source_id(cur, "EU_ETS")
    base = ROOT / "sources" / "step12-emissions"
    p = first_existing([
        base / "silver" / "eea_eu_ets" / "sheet1.parquet",
        base / "data" / "silver" / "eea_eu_ets" / "sheet1.parquet",
    ])
    if not p:
        raise FileNotFoundError("Could not locate EU ETS Silver parquet.")
    cur.execute("DELETE FROM ref_eu_ets WHERE source_dataset_id=%s", (sid,))
    df = pd.read_parquet(p)
    insert_json_rows(cur, "ref_eu_ets", sid, df)
    return len(df)


def load_eurostat(cur):
    sid = source_id(cur, "EUROSTAT_ENERGY_PRICES")
    base = ROOT / "sources" / "step14-eu-energy-prices"
    silver_candidates = [
        base / "silver",
        base / "data" / "silver",
    ]
    silver_root = next((p for p in silver_candidates if p.exists()), None)
    if silver_root is None:
        raise FileNotFoundError("Could not locate Eurostat Silver folder.")

    cur.execute(
        "DELETE FROM ref_eurostat_energy_price WHERE source_dataset_id=%s", (sid,))
    count = 0
    files = sorted(silver_root.rglob("*.parquet"))
    for p in files:
        code = "nrg_pc_205" if "205" in p.name else (
            "nrg_pc_203" if "203" in p.name else p.stem)
        df = pd.read_parquet(p)
        insert_json_rows(cur, "ref_eurostat_energy_price",
                         sid, df, {"dataset_code": code})
        count += len(df)
    if count == 0:
        print("Eurostat note: current Step 14 Silver may contain metadata-only outputs, so zero expanded rows is acceptable at Stage 4F.")
    return count, len(files)


def print_counts(cur):
    tables = [
        "ref_itac_assessment",
        "ref_itac_recommendation",
        "ref_fmucd_maintenance",
        "ref_statcan_water",
        "ref_eia_mecs",
        "ref_eu_ets",
        "ref_eurostat_energy_price",
    ]
    print("\nReference table row counts")
    print("--------------------------")
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"{t:32s} {cur.fetchone()[0]:,}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5433)
    parser.add_argument("--dbname", default="manufacturing_intelligence")
    parser.add_argument("--user", default="postgres")
    args = parser.parse_args()

    with psycopg.connect(**connection_parameters(args)) as conn:
        with conn.cursor() as cur:
            print("Loading ITAC ...")
            a, r = load_itac(cur)
            print(f"  assessments: {a:,}")
            print(f"  recommendations: {r:,}")

            print("Loading FMUCD ...")
            n = load_fmucd(cur)
            print(f"  rows: {n:,}")

            print("Loading StatCan water ...")
            n = load_statcan(cur)
            print(f"  rows: {n:,}")

            print("Loading EIA MECS ...")
            n, files = load_mecs(cur)
            print(f"  rows: {n:,} across {files} parquet files")

            print("Loading EU ETS ...")
            n = load_euets(cur)
            print(f"  rows: {n:,}")

            print("Loading Eurostat energy-price Silver ...")
            n, files = load_eurostat(cur)
            print(f"  rows: {n:,} across {files} parquet files")

            print_counts(cur)

    print("\nStage 4F reference/benchmark load complete.")


if __name__ == "__main__":
    main()
