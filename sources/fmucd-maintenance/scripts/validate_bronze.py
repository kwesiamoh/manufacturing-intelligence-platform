"""Lightweight validation of the raw FMUCD CSV without loading it into memory."""
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
files = list((ROOT / "bronze").glob("*.csv"))
if not files:
    raise SystemExit("No Bronze CSV found. Run download_fmucd.py first.")

path = files[0]
with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
    reader = csv.reader(f)
    header = next(reader)

required_candidates = {
    "WOID",
    "WODescription",
    "WOPriority",
    "WOStartDate",
    "WODuration",
    "LaborCost",
    "MaterialCost",
    "TotalCost",
}
missing = sorted(required_candidates - set(header))
print("file:", path.name)
print("size_bytes:", path.stat().st_size)
print("column_count:", len(header))
print("missing_expected_columns:", missing)
if missing:
    raise SystemExit(2)
print("Bronze header validation passed.")
