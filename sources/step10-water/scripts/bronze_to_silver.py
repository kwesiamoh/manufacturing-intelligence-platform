#!/usr/bin/env python3
from pathlib import Path
import re
import zipfile
import tempfile
import polars as pl

ARCHIVE = Path("bronze/statcan_industrial_water/38100056-eng.zip")
SILVER = Path("silver/statcan_industrial_water")
SILVER.mkdir(parents=True, exist_ok=True)


def snake(name):
    name = str(name).strip()
    name = re.sub(r"[^0-9A-Za-z]+", "_", name)
    return re.sub(r"_+", "_", name).strip("_").lower()


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    with zipfile.ZipFile(ARCHIVE) as zf:
        zf.extractall(td)

    csv_files = list(td.rglob("*.csv"))
    if not csv_files:
        raise SystemExit("No CSV found after extraction.")

    for src in csv_files:
        # Infer schema conservatively; preserve source strings/flags.
        df = pl.read_csv(
            src,
            infer_schema_length=10000,
            null_values=["..", "..."],
            ignore_errors=False,
            encoding="utf8-lossy",
            truncate_ragged_lines=True,
        )

        rename_map = {c: snake(c) for c in df.columns}
        df = df.rename(rename_map)

        # No imputation, aggregation, unit conversion, or filtering is done here.
        out = SILVER / f"{snake(src.stem)}.parquet"
        df.write_parquet(out, compression="zstd")
        print(f"{src.name}: {df.height:,} rows -> {out}")

print("Silver conversion complete.")
