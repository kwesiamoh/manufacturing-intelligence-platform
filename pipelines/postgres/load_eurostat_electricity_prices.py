from pathlib import Path
import argparse
import pandas as pd
import psycopg

from connection_auth import connection_parameters

ROOT = Path(__file__).resolve().parents[2]
PATH = (
    ROOT / "sources" / "eurostat-energy-prices" / "silver"
    / "eurostat_energy_prices"
    / "nrg_pc_205__six_site_countries_2024_2025.parquet"
)

TARGET_GEOS = {"DE", "NL", "PL", "CZ", "FR", "ES"}
TARGET_BAND = "MWH2000-19999"
TARGET_UNIT = "KWH"
TARGET_TAX = "X_VAT"
TARGET_CURRENCY = "EUR"

def source_id(cur):
    cur.execute(
        "SELECT source_dataset_id FROM dim_source_dataset "
        "WHERE source_code='EUROSTAT_ENERGY_PRICES'"
    )
    row = cur.fetchone()
    if not row:
        raise RuntimeError("Missing EUROSTAT_ENERGY_PRICES in dim_source_dataset.")
    return row[0]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5433)
    parser.add_argument("--dbname", default="manufacturing_intelligence")
    parser.add_argument("--user", default="postgres")
    args = parser.parse_args()

    if not PATH.exists():
        raise FileNotFoundError(PATH)

    df = pd.read_parquet(PATH)

    selected = df[
        df["geo"].isin(TARGET_GEOS)
        & (df["nrg_cons"] == TARGET_BAND)
        & (df["unit"] == TARGET_UNIT)
        & (df["tax"] == TARGET_TAX)
        & (df["currency"] == TARGET_CURRENCY)
    ].copy()

    expected_periods = {"2024-S1", "2024-S2", "2025-S1", "2025-S2"}

    print("Selected Eurostat observations:", len(selected))
    print("Countries:", sorted(selected["geo"].unique().tolist()))
    print("Periods:", sorted(selected["time"].unique().tolist()))
    print("Band:", TARGET_BAND)
    print("Tax basis:", TARGET_TAX)
    print("Currency:", TARGET_CURRENCY)
    print("Unit:", TARGET_UNIT)

    if set(selected["geo"].unique()) != TARGET_GEOS:
        raise RuntimeError("Missing one or more target countries.")
    if set(selected["time"].unique()) != expected_periods:
        raise RuntimeError("Missing one or more expected semesters.")
    if len(selected) != 24:
        raise RuntimeError(f"Expected 24 country-semester observations; found {len(selected)}.")

    with psycopg.connect(**connection_parameters(args)) as conn:
        with conn.cursor() as cur:
            sid = source_id(cur)

            cur.execute(
                "DELETE FROM ref_eurostat_electricity_price_observation "
                "WHERE source_dataset_id=%s",
                (sid,)
            )

            sql = """
                INSERT INTO ref_eurostat_electricity_price_observation (
                    source_dataset_id, dataset_code, geo_code, geo_name,
                    period_code, frequency_code, energy_product_code,
                    consumption_band_code, consumption_band_label,
                    unit_code, unit_label, tax_code, tax_label,
                    currency_code, currency_label, price_value, status_code,
                    data_class, integration_role
                )
                VALUES (
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,%s,%s,%s
                )
            """

            rows = []
            for r in selected.itertuples(index=False):
                rows.append((
                    sid,
                    "nrg_pc_205",
                    r.geo,
                    r.geo_label,
                    r.time,
                    r.freq,
                    r.siec,
                    r.nrg_cons,
                    r.nrg_cons_label,
                    r.unit,
                    r.unit_label,
                    r.tax,
                    r.tax_label,
                    r.currency,
                    r.currency_label,
                    float(r.value),
                    None if pd.isna(r.status) else str(r.status),
                    "REAL_EXTERNAL_BENCHMARK",
                    "BENCHMARK",
                ))

            cur.executemany(sql, rows)

    print("\nenergy-cost Eurostat price-observation load complete.")

if __name__ == "__main__":
    main()
