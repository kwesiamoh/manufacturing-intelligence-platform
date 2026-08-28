from __future__ import annotations

import hashlib
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "bronze" / "production_downtime" / "production_raw.xlsx"
EXPECTED_MD5 = "d9c095d5eba8706ac7dda92af63f5c35"

EXPECTED = {
    "processed_hourly": {"date", "hour_start", "hour_end", "production_gallons"},
    "daily_operation_summary": {
        "date", "product_type_l", "production_units", "liters_produced",
        "production_start_time", "production_end_time", "efficiency",
        "gallons_per_hour", "monitored_time_dec", "operation_time_dec",
        "pause_time_dec"
    },
    "hourly_operation_breakdown": {
        "date", "hour_start", "hour_end", "monitored_time_h",
        "operation_time_h", "downtime_h", "efficiency"
    },
    "downtime_event_log": {
        "downtime_id", "date", "downtime_start_time", "downtime_end_time",
        "downtime_time"
    },
}


def md5sum(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    if not SRC.exists():
        raise FileNotFoundError(f"Missing Bronze file: {SRC}")
    digest = md5sum(SRC)
    if digest != EXPECTED_MD5:
        raise RuntimeError(f"Bronze MD5 mismatch: {digest}")

    for sheet, required in EXPECTED.items():
        df = pl.read_excel(SRC, sheet_name=sheet, engine="calamine")
        missing = required.difference(df.columns)
        if missing:
            raise RuntimeError(f"{sheet}: missing columns {sorted(missing)}")
        if df.height == 0:
            raise RuntimeError(f"{sheet}: sheet is empty")
        print(f"{sheet}: {df.height:,} rows; schema OK")

    print("Bronze validation passed.")


if __name__ == "__main__":
    main()
