#!/usr/bin/env python3
from pathlib import Path
import re
import polars as pl

BRONZE = Path("bronze/industrial_park_ies")
SILVER = Path("silver/industrial_park_ies")
SILVER.mkdir(parents=True, exist_ok=True)

FILES = {
    "preair_G.xlsx": "compressed_air_flow",
    "preair_P.xlsx": "compressed_air_pressure",
    "steam_G.xlsx": "steam_flow",
    "steam_P.xlsx": "steam_pressure",
}

def snake(name):
    text = str(name).strip()
    text = re.sub(r"[^0-9A-Za-z]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_").lower()

for filename, logical_name in FILES.items():
    src = BRONZE / filename

    # Polars uses the fastexcel engine for .xlsx input.
    sheets = pl.read_excel(src, sheet_id=0)
    if isinstance(sheets, dict):
        items = sheets.items()
    else:
        items = [("sheet1", sheets)]

    for sheet_name, df in items:
        df = df.rename({c: snake(c) for c in df.columns})
        # Preserve all source values. No imputation, unit conversion, interpolation,
        # timestamp fabrication, or outlier removal is performed here.
        out = SILVER / f"{logical_name}__{snake(sheet_name)}.parquet"
        df.write_parquet(out, compression="zstd")
        print(f"{filename} / {sheet_name}: {df.height:,} rows -> {out}")

print("Silver conversion complete.")
