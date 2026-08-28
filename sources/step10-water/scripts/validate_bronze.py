#!/usr/bin/env python3
from pathlib import Path
import csv
import zipfile

archive = Path("bronze/statcan_industrial_water/38100056-eng.zip")
if not archive.exists():
    raise SystemExit("Bronze archive not found. Run scripts/download_statcan.py first.")

if not zipfile.is_zipfile(archive):
    raise SystemExit("Downloaded source is not a valid ZIP.")

with zipfile.ZipFile(archive) as zf:
    names = zf.namelist()
    csv_files = [n for n in names if n.lower().endswith(".csv")]
    if not csv_files:
        raise SystemExit("No CSV found inside Statistics Canada archive.")

    print("CSV files:")
    for name in csv_files:
        print(" -", name)

    # Inspect first CSV header without altering source.
    with zf.open(csv_files[0]) as raw:
        import io
        text = io.TextIOWrapper(raw, encoding="utf-8-sig")
        reader = csv.reader(text)
        header = next(reader)
        print("header columns:", len(header))
        print(header)

print("Bronze container validation passed.")
