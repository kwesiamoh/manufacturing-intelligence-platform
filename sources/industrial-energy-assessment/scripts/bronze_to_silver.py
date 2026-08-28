#!/usr/bin/env python3
from pathlib import Path
import re
import tempfile
import zipfile
import pandas as pd

ARCHIVE = Path("bronze/itac/ITAC_Database.zip")
SILVER = Path("silver/itac")
SILVER.mkdir(parents=True, exist_ok=True)

def snake(s):
    s = str(s).strip()
    s = re.sub(r"[^0-9A-Za-z]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_").lower()

with tempfile.TemporaryDirectory(prefix="itac-extract-") as temporary_directory:
    extracted = Path(temporary_directory)
    with zipfile.ZipFile(ARCHIVE) as zf:
        zf.extractall(extracted)

    workbooks = list(extracted.rglob("*.xlsx")) + list(extracted.rglob("*.xls"))
    if not workbooks:
        raise SystemExit("No workbook found after extraction.")

    for workbook in workbooks:
        xl = pd.ExcelFile(workbook)
        for sheet in xl.sheet_names:
            df = pd.read_excel(workbook, sheet_name=sheet)
            df.columns = [snake(c) for c in df.columns]

            # Preserve source values; only normalize column names and remove completely blank rows.
            df = df.dropna(how="all")

            out_name = f"{snake(workbook.stem)}__{snake(sheet)}.parquet"
            out = SILVER / out_name
            df.to_parquet(out, index=False)
            print(f"{sheet}: {len(df):,} rows -> {out}")

print("Silver conversion complete.")
