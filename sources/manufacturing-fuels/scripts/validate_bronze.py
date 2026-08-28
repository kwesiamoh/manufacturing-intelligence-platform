#!/usr/bin/env python3
from pathlib import Path
import zipfile

base = Path("bronze/eia_mecs_2022")
expected = ["Table3_1.xlsx", "Table7_3.xlsx", "Table7_7.xlsx", "Table7_10.xlsx"]

for filename in expected:
    p = base / filename
    if not p.exists():
        raise SystemExit(f"Missing Bronze workbook: {p}")
    if not zipfile.is_zipfile(p):
        raise SystemExit(f"Invalid XLSX container: {p}")
    print(f"{filename}: valid XLSX container, {p.stat().st_size:,} bytes")

print("Bronze validation passed.")
