from pathlib import Path
import argparse
import getpass
import json
import math

import numpy as np
import pandas as pd
import psycopg

from dq_exit_semantics import exit_code_for_statuses

ROOT = Path(__file__).resolve().parents[2]
STEP = ROOT / "sources" / "step02-telemetry"

KNOWN_TIMESTAMP_NAMES = [
    "timestamp", "Timestamp", "datetime", "date_time", "DateTime", "time"
]

# Silver column names are normalized to lowercase.
METADATA_COLUMNS = {
    "unnamed_0", "year", "month"
}

DISCRETE_OR_STATE_COLUMNS = {
    "comp", "dv_eletric", "towers", "mpg", "lps",
    "pressure_switch", "oil_level"
}

EVENT_COUNTER_COLUMNS = {
    "caudal_impulses"
}

# Genuine analog channels in MetroPT-3.
ANALOG_COLUMNS = {
    "tp2", "tp3", "h1", "dv_pressure", "reservoirs",
    "oil_temperature", "motor_current"
}

def find_parquet():
    files = sorted(STEP.rglob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"No parquet files found under {STEP}")
    metro = [p for p in files if "metro" in str(p).lower()]
    return metro if metro else files

def timestamp_column(df):
    for c in KNOWN_TIMESTAMP_NAMES:
        if c in df.columns:
            return c
    dtcols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    if len(dtcols) == 1:
        return dtcols[0]
    raise RuntimeError(f"Could not identify timestamp column. Columns: {list(df.columns)}")

def contiguous_true_run_lengths(mask):
    arr = np.asarray(mask, dtype=bool)
    if arr.size == 0:
        return np.array([], dtype=int)
    padded = np.r_[False, arr, False]
    changes = np.flatnonzero(padded[1:] != padded[:-1])
    return changes[1::2] - changes[::2]

def insert_result(cur, code, sid, evaluated, failed, status, detail):
    cur.execute("SELECT dq_rule_id FROM dq_rule WHERE rule_code=%s", (code,))
    rid = cur.fetchone()[0]
    rate = failed / evaluated if evaluated else 0
    cur.execute("""
        INSERT INTO dq_result
        (dq_rule_id, source_dataset_id, target_object, evaluated_row_count,
         failed_row_count, failure_rate, result_status, result_detail)
        VALUES (%s,%s,'MetroPT-3 Silver',%s,%s,%s,%s,%s)
    """, (rid, sid, evaluated, failed, rate, status, detail))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=5433)
    ap.add_argument("--dbname", default="manufacturing_intelligence")
    ap.add_argument("--user", default="postgres")
    args = ap.parse_args()

    files = find_parquet()
    print("MetroPT parquet files found:")
    for p in files:
        print(" ", p)

    df = pd.concat([pd.read_parquet(p) for p in files], ignore_index=True)
    print(f"\nRows loaded: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    ts_col = timestamp_column(df)
    df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")
    print("Timestamp column:", ts_col)

    timestamp_nulls = int(df[ts_col].isna().sum())
    timestamp_dups = int(df.loc[df[ts_col].notna(), ts_col].duplicated().sum())

    valid = df[df[ts_col].notna()].sort_values(ts_col).reset_index(drop=True)
    deltas = valid[ts_col].diff().dt.total_seconds().dropna()
    median_interval = float(deltas.median()) if len(deltas) else np.nan
    gap_threshold = median_interval * 1.5 if np.isfinite(median_interval) else np.nan
    gap_mask = deltas > gap_threshold if np.isfinite(gap_threshold) else pd.Series(False, index=deltas.index)
    gap_count = int(gap_mask.sum())
    max_gap = float(deltas.max()) if len(deltas) else np.nan

    numeric_cols = [
        c for c in valid.columns
        if c != ts_col
        and c not in METADATA_COLUMNS
        and pd.api.types.is_numeric_dtype(valid[c])
    ]

    analog_cols = [c for c in numeric_cols if c in ANALOG_COLUMNS]
    discrete_cols = [c for c in numeric_cols if c in DISCRETE_OR_STATE_COLUMNS]
    event_cols = [c for c in numeric_cols if c in EVENT_COUNTER_COLUMNS]
    unclassified_cols = [
        c for c in numeric_cols
        if c not in ANALOG_COLUMNS
        and c not in DISCRETE_OR_STATE_COLUMNS
        and c not in EVENT_COUNTER_COLUMNS
    ]

    total_numeric_cells = len(valid) * len(numeric_cols)
    missing_numeric = int(valid[numeric_cols].isna().sum().sum()) if numeric_cols else 0

    # Frozen analog screening: unchanged for >=10 minutes.
    frozen_minutes = 10
    frozen_run_samples = max(2, math.ceil((frozen_minutes * 60) / median_interval))

    frozen_detail = {}
    frozen_events = 0

    for c in analog_cols:
        s = valid[c]
        same = s.eq(s.shift(1)) & s.notna() & s.shift(1).notna()
        runs = contiguous_true_run_lengths(same.to_numpy())
        long_runs = runs[runs + 1 >= frozen_run_samples]
        n = int(len(long_runs))
        if n:
            frozen_detail[c] = {
                "event_count": n,
                "max_unchanged_samples": int(long_runs.max() + 1),
                "max_unchanged_minutes": float((long_runs.max() + 1) * median_interval / 60.0),
            }
            frozen_events += n

    # Conservative spike diagnostic.
    # Use 0.01% and 99.99% empirical first-difference tails per analog channel.
    # This deliberately labels findings as diagnostic WARN only, not bad data.
    spike_detail = {}
    spike_events = 0

    for c in analog_cols:
        x = pd.to_numeric(valid[c], errors="coerce")
        diff = x.diff()
        finite = diff.dropna()
        if len(finite) < 1000:
            continue

        lo = float(finite.quantile(0.0001))
        hi = float(finite.quantile(0.9999))
        flags = (diff < lo) | (diff > hi)
        n = int(flags.sum())

        if n:
            spike_detail[c] = {
                "diagnostic_event_count": n,
                "lower_delta_quantile_0_01pct": lo,
                "upper_delta_quantile_99_99pct": hi,
            }
            spike_events += n

    outdir = ROOT / "data_quality" / "metropt"
    outdir.mkdir(parents=True, exist_ok=True)

    summary = {
        "rows": len(df),
        "timestamp_column": ts_col,
        "timestamp_nulls": timestamp_nulls,
        "duplicate_timestamps": timestamp_dups,
        "median_interval_seconds": median_interval,
        "gap_threshold_seconds": gap_threshold,
        "gap_count": gap_count,
        "max_gap_seconds": max_gap,
        "numeric_sensor_columns": numeric_cols,
        "analog_columns_checked": analog_cols,
        "discrete_state_columns_excluded_from_analog_checks": discrete_cols,
        "event_counter_columns_excluded_from_analog_checks": event_cols,
        "metadata_columns_excluded": sorted(METADATA_COLUMNS),
        "unclassified_numeric_columns": unclassified_cols,
        "missing_numeric_cells": missing_numeric,
        "frozen_run_threshold_samples": frozen_run_samples,
        "frozen_run_threshold_minutes": frozen_minutes,
        "frozen_event_count": frozen_events,
        "frozen_detail": frozen_detail,
        "spike_diagnostic_event_count": spike_events,
        "spike_diagnostic_detail": spike_detail,
        "spike_method": "empirical first-difference tails below 0.01 percentile or above 99.99 percentile; diagnostic only",
    }

    (outdir / "metropt_dq_summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )

    if gap_count:
        gap_rows = valid.loc[gap_mask.index[gap_mask], [ts_col]].copy()
        gap_rows["gap_seconds"] = deltas.loc[gap_mask].values
        gap_rows.to_parquet(outdir / "metropt_timestamp_gaps.parquet", index=False)

    password = getpass.getpass(f"\nPassword for PostgreSQL user {args.user}: ")

    result_statuses = [
        "PASS" if timestamp_nulls == 0 else "FAIL",
        "PASS" if timestamp_dups == 0 else "FAIL",
        "PASS" if gap_count == 0 else "WARN",
        "PASS" if missing_numeric == 0 else "WARN",
        "PASS" if frozen_events == 0 else "WARN",
        "PASS" if spike_events == 0 else "WARN",
    ]

    with psycopg.connect(
        host=args.host, port=args.port, dbname=args.dbname,
        user=args.user, password=password
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT source_dataset_id FROM dim_source_dataset "
                "WHERE source_code='METROPT3'"
            )
            sid = cur.fetchone()[0]

            cur.execute("""
                DELETE FROM dq_result
                WHERE dq_rule_id IN (
                    SELECT dq_rule_id FROM dq_rule
                    WHERE rule_code LIKE 'METROPT_%'
                )
            """)

            insert_result(
                cur, "METROPT_TIMESTAMP_NULL", sid, len(df), timestamp_nulls,
                result_statuses[0],
                f"Timestamp column: {ts_col}"
            )
            insert_result(
                cur, "METROPT_TIMESTAMP_DUP", sid, len(valid), timestamp_dups,
                result_statuses[1],
                "Duplicate timestamps are structural DQ failures."
            )
            insert_result(
                cur, "METROPT_INTERVAL_GAP", sid, max(len(valid)-1, 0), gap_count,
                result_statuses[2],
                f"Median cadence={median_interval}s; gap threshold={gap_threshold}s; max gap={max_gap}s."
            )
            insert_result(
                cur, "METROPT_SENSOR_NULL", sid, total_numeric_cells, missing_numeric,
                result_statuses[3],
                f"Numeric sensor cells checked={total_numeric_cells}; metadata columns excluded."
            )
            insert_result(
                cur, "METROPT_SENSOR_FROZEN", sid,
                len(valid) * max(len(analog_cols), 1),
                frozen_events,
                result_statuses[4],
                f"Analog channels checked={analog_cols}; threshold={frozen_minutes} min."
            )
            insert_result(
                cur, "METROPT_SENSOR_SPIKE", sid,
                len(valid) * max(len(analog_cols), 1),
                spike_events,
                result_statuses[5],
                "Diagnostic only: empirical first-difference 0.01%/99.99% tails on analog channels."
            )

    print("\nCorrected Stage 7B MetroPT DQ summary")
    print("-------------------------------------")
    print(f"Timestamp nulls:       {timestamp_nulls:,}")
    print(f"Duplicate timestamps: {timestamp_dups:,}")
    print(f"Median interval:       {median_interval:.3f} s")
    print(f"Timestamp gaps:        {gap_count:,}")
    print(f"Maximum gap:           {max_gap:.3f} s")
    print(f"Missing numeric cells: {missing_numeric:,}")
    print(f"Analog channels:       {analog_cols}")
    print(f"Frozen events:         {frozen_events:,}")
    print(f"Spike diagnostics:     {spike_events:,}")
    print(f"\nDetail summary: {outdir / 'metropt_dq_summary.json'}")
    print("\nStructural failures are FAIL; time-series findings are WARN.")
    overall = "FAIL" if "FAIL" in result_statuses else "PASS"
    print("Overall Stage 7B DQ result:", overall)

    raise SystemExit(exit_code_for_statuses(result_statuses))

if __name__ == "__main__":
    main()
