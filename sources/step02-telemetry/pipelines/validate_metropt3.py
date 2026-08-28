from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = ROOT / "data" / "bronze" / "metropt3" / "MetroPT3(AirCompressor).csv"
DEFAULT_REPORT = ROOT / "data" / "bronze" / "metropt3" / "validation_report.json"
EXPECTED_ROWS = 1_516_948


def validate(raw: Path, report_path: Path, expected_rows: int) -> str:
    if not raw.is_file():
        raise FileNotFoundError(
            f"Raw source not found: {raw}\n"
            "Run ingestion/batch/download_metropt3.py first."
        )

    frame = pd.read_csv(raw)
    column_lookup = {column.strip().lower(): column for column in frame.columns}
    timestamp_column = column_lookup.get("timestamp")
    if timestamp_column is None:
        raise ValueError(
            f"No timestamp column found. Source columns: {list(frame.columns)}"
        )

    timestamps = pd.to_datetime(frame[timestamp_column], errors="coerce")
    valid_timestamps = timestamps.dropna().sort_values()
    deltas = valid_timestamps.diff().dt.total_seconds().dropna()

    report = {
        "rows": int(len(frame)),
        "expected_rows": expected_rows,
        "row_count_matches_uci": bool(len(frame) == expected_rows),
        "columns": list(frame.columns),
        "column_count": int(len(frame.columns)),
        "missing_cells": int(frame.isna().sum().sum()),
        "duplicate_rows": int(frame.duplicated().sum()),
        "invalid_timestamps": int(timestamps.isna().sum()),
        "timestamp_min": (
            valid_timestamps.min().isoformat() if len(valid_timestamps) else None
        ),
        "timestamp_max": (
            valid_timestamps.max().isoformat() if len(valid_timestamps) else None
        ),
        "median_sampling_interval_seconds": (
            float(deltas.median()) if len(deltas) else None
        ),
        "minimum_sampling_interval_seconds": (
            float(deltas.min()) if len(deltas) else None
        ),
        "maximum_sampling_interval_seconds": (
            float(deltas.max()) if len(deltas) else None
        ),
    }

    failures = []
    warnings = []
    if not report["row_count_matches_uci"]:
        failures.append(
            f"expected {expected_rows:,} rows, observed {report['rows']:,}"
        )
    if report["invalid_timestamps"]:
        failures.append(f"invalid timestamps: {report['invalid_timestamps']:,}")
    if not valid_timestamps.size:
        failures.append("no valid timestamps")
    if report["duplicate_rows"]:
        warnings.append(f"duplicate rows: {report['duplicate_rows']:,}")
    if report["missing_cells"]:
        warnings.append(f"missing cells: {report['missing_cells']:,}")

    status = "FAIL" if failures else ("WARN" if warnings else "PASS")
    report["failures"] = failures
    report["warnings"] = warnings
    report["validation_status"] = status
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

    if failures:
        raise RuntimeError("; ".join(failures))
    if warnings:
        print("WARN: structural validation passed with informational findings")
    else:
        print("PASS: MetroPT-3 Bronze validation passed")
    return status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate MetroPT-3 Bronze CSV")
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--expected-rows", type=int, default=EXPECTED_ROWS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        validate(args.raw, args.report, args.expected_rows)
        return 0
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as exc:
        print(f"FAIL: MetroPT-3 Bronze validation failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
