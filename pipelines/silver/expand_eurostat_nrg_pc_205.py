from pathlib import Path
import itertools
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BRONZE = ROOT / "sources" / "step14-eu-energy-prices" / "bronze" / "eurostat_energy_prices" / "nrg_pc_205__full.json"
SILVER_DIR = ROOT / "sources" / "step14-eu-energy-prices" / "silver" / "eurostat_energy_prices"
SILVER_DIR.mkdir(parents=True, exist_ok=True)

TARGET_GEOS = {"DE", "NL", "PL", "CZ", "FR", "ES"}
TARGET_YEARS = {"2024", "2025"}

def ordered_codes(dim):
    idx = dim["category"]["index"]
    if isinstance(idx, list):
        return idx
    return [k for k, _ in sorted(idx.items(), key=lambda kv: kv[1])]

def decode_jsonstat(payload):
    ids = payload["id"]
    sizes = payload["size"]
    dims = payload["dimension"]
    codes = [ordered_codes(dims[d]) for d in ids]

    values = payload.get("value", {})
    statuses = payload.get("status", {})

    rows = []
    for flat_idx_str, value in values.items():
        flat_idx = int(flat_idx_str)
        coords = []
        rem = flat_idx
        for size in reversed(sizes):
            coords.append(rem % size)
            rem //= size
        coords = list(reversed(coords))

        row = {}
        for d, pos, code_list in zip(ids, coords, codes):
            code = code_list[pos]
            row[d] = code
            labels = dims[d]["category"].get("label", {})
            row[f"{d}_label"] = labels.get(code, code)

        row["value"] = value
        row["status"] = statuses.get(flat_idx_str)
        rows.append(row)

    return pd.DataFrame(rows)

def main():
    if not BRONZE.exists():
        raise FileNotFoundError(
            f"{BRONZE}\nRun download_eurostat_nrg_pc_205.py first."
        )

    payload = json.loads(BRONZE.read_text(encoding="utf-8"))
    df = decode_jsonstat(payload)

    print("Decoded rows:", f"{len(df):,}")
    print("Columns:", list(df.columns))

    if "geo" not in df.columns:
        raise RuntimeError("Eurostat response does not contain expected 'geo' dimension.")
    if "time" not in df.columns:
        raise RuntimeError("Eurostat response does not contain expected 'time' dimension.")

    df["reference_year"] = df["time"].astype(str).str[:4]

    six = df[
        df["geo"].isin(TARGET_GEOS)
        & df["reference_year"].isin(TARGET_YEARS)
    ].copy()

    if six.empty:
        raise RuntimeError("No 2024-2025 observations found for the six target countries.")

    six["dataset_code"] = "nrg_pc_205"
    six["data_class"] = "REAL_EXTERNAL_BENCHMARK"
    six["integration_role"] = "BENCHMARK"

    all_path = SILVER_DIR / "nrg_pc_205__observations.parquet"
    six_path = SILVER_DIR / "nrg_pc_205__six_site_countries_2024_2025.parquet"

    df.to_parquet(all_path, index=False)
    six.to_parquet(six_path, index=False)

    print("\nWrote full decoded Silver:", all_path)
    print("Wrote six-country 2024-2025 Silver:", six_path)
    print("Six-country rows:", f"{len(six):,}")

    print("\nUnique values by dimension in filtered output:")
    for d in payload["id"]:
        if d in six.columns:
            vals = sorted(six[d].dropna().astype(str).unique().tolist())
            print(f"{d}: {vals}")

    print("\nTime periods:", sorted(six["time"].astype(str).unique().tolist()))

if __name__ == "__main__":
    main()
