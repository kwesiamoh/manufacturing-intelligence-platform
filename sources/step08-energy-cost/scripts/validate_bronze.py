#!/usr/bin/env python3
from pathlib import Path
import zipfile
import hashlib
import sys

archive = Path("bronze/itac/ITAC_Database.zip")
if not archive.exists():
    raise SystemExit("Bronze archive not found. Run scripts/download_itac.py first.")

if not zipfile.is_zipfile(archive):
    raise SystemExit("Downloaded file is not a valid ZIP archive.")

with zipfile.ZipFile(archive) as zf:
    names = zf.namelist()
    workbooks = [n for n in names if n.lower().endswith((".xlsx", ".xls"))]
    if not workbooks:
        raise SystemExit("No Excel workbook found inside ITAC archive.")
    print("workbooks:")
    for n in workbooks:
        print(" -", n)

h = hashlib.sha256()
with archive.open("rb") as f:
    for chunk in iter(lambda: f.read(1024 * 1024), b""):
        h.update(chunk)

print(f"bytes={archive.stat().st_size}")
print(f"sha256={h.hexdigest()}")
print("Bronze validation passed.")
