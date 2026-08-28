#!/usr/bin/env python3
from pathlib import Path
import re
import pandas as pd

BRONZE = Path("bronze/eia_mecs_2022")
SILVER = Path("silver/eia_mecs_2022")
SILVER.mkdir(parents=True, exist_ok=True)


def snake(text):
    text = str(text).strip()
    text = re.sub(r"[^0-9A-Za-z]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_").lower()


for workbook in sorted(BRONZE.glob("*.xlsx")):
    xl = pd.ExcelFile(workbook)
    for sheet in xl.sheet_names:
        raw = pd.read_excel(workbook, sheet_name=sheet, header=None, dtype=str)
        raw = raw.dropna(how="all").dropna(axis=1, how="all")
        out = SILVER / f"{snake(workbook.stem)}__{snake(sheet)}.parquet"
        raw.to_parquet(out, index=False)
        print(
            f"{workbook.name} / {sheet}: {raw.shape[0]:,} rows x {raw.shape[1]:,} cols -> {out}")

print("Conservative Silver conversion complete.")
print("Interpret EIA headers and footnotes only in a later schema-mapping step.")
