from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Stage 12C.2 — causal adaptive alerting for the existing Isolation Forest
#
# Motivation:
# The Stage 12C model detects all four failures, but a fixed threshold calibrated
# on February produces excessive false alarms after the score distribution
# shifts in later months.
#
# This revision DOES NOT retrain the Isolation Forest and DOES NOT use known
# failure outcomes to select the threshold.
#
# Decision rule:
#   - use the existing Isolation Forest anomaly score
#   - adaptive threshold = 99.5th percentile of the preceding 7 days
#   - introduce a 24-hour lag before score history may influence the threshold
#   - require >=3 anomalous bins in the trailing 4 bins for an alert
#
# The 24-hour lag prevents the current developing event from immediately
# inflating its own threshold.
# ---------------------------------------------------------------------------

LOOKBACK_BINS = 7 * 24 * 12          # 7 days at 5-min bins
LAG_BINS = 24 * 12                   # 24-hour exclusion lag
MIN_HISTORY_BINS = 3 * 24 * 12       # at least 3 days of historical scores
ADAPTIVE_QUANTILE = 0.995

ALERT_WINDOW_BINS = 4
ALERT_REQUIRED_BINS = 3

WARNING_HORIZON_HOURS = 24
TARGET_LEAD_HOURS = 2


def find_repo_root() -> Path:
    here = Path.cwd()
    for candidate in [here, *here.parents]:
        if (candidate / "sources").exists() and (candidate / "data").exists():
            return candidate
    raise FileNotFoundError("Run from the manufacturing-intelligence-platform repository.")


def parse_failure_windows(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path)
    d.columns = [
        str(c).strip().lower().replace(" ", "_").replace("-", "_")
        for c in d.columns
    ]

    start_candidates = [
        "start", "start_time", "start_timestamp", "failure_start",
        "failure_start_time", "failure_start_timestamp", "begin", "begin_time",
    ]
    end_candidates = [
        "end", "end_time", "end_timestamp", "failure_end",
        "failure_end_time", "failure_end_timestamp", "finish", "finish_time",
    ]
    id_candidates = ["failure_id", "event_id", "id", "failure", "event"]

    start_col = next((c for c in start_candidates if c in d.columns), None)
    end_col = next((c for c in end_candidates if c in d.columns), None)
    id_col = next((c for c in id_candidates if c in d.columns), None)

    if start_col is None or end_col is None:
        dt_cols = []
        for c in d.columns:
            p = pd.to_datetime(d[c], errors="coerce")
            if p.notna().mean() >= 0.8:
                dt_cols.append(c)
        if len(dt_cols) < 2:
            raise ValueError(f"Cannot infer failure start/end columns: {list(d.columns)}")
        start_col, end_col = dt_cols[:2]

    out = pd.DataFrame()
    out["failure_start"] = pd.to_datetime(d[start_col], errors="coerce")
    out["failure_end"] = pd.to_datetime(d[end_col], errors="coerce")
    if id_col:
        out["failure_id"] = d[id_col].astype(str)
    else:
        out["failure_id"] = [str(i + 1) for i in range(len(out))]

    return out.dropna(subset=["failure_start", "failure_end"])


def persistent_alert(raw: pd.Series) -> pd.Series:
    return (
        raw.astype("int8")
        .rolling(ALERT_WINDOW_BINS, min_periods=ALERT_WINDOW_BINS)
        .sum()
        .ge(ALERT_REQUIRED_BINS)
    )


def event_evaluation(
    d: pd.DataFrame,
    failures: pd.DataFrame,
    alert_col: str,
) -> pd.DataFrame:
    rows = []
    for _, f in failures.iterrows():
        start = f["failure_start"]
        end = f["failure_end"]
        if end < d.index.min() or start > d.index.max():
            continue

        warning_start = start - pd.Timedelta(hours=WARNING_HORIZON_HOURS)
        hits = d.loc[
            (d.index >= warning_start)
            & (d.index <= end)
            & d[alert_col]
        ]

        if len(hits):
            first = hits.index[0]
            lead = (start - first).total_seconds() / 3600.0
            detected = True
            early = lead >= TARGET_LEAD_HOURS
        else:
            first = pd.NaT
            lead = np.nan
            detected = False
            early = False

        rows.append({
            "failure_id": f["failure_id"],
            "failure_start": start,
            "failure_end": end,
            "detected_within_24h_or_during": detected,
            "detected_at_least_2h_early": early,
            "first_alert_timestamp": first,
            "lead_time_hours": lead,
        })

    return pd.DataFrame(rows)


def episode_starts(alert: pd.Series) -> pd.DatetimeIndex:
    return alert.index[alert & ~alert.shift(1, fill_value=False)]


def false_alert_metrics(
    d: pd.DataFrame,
    failures: pd.DataFrame,
    alert_col: str,
) -> tuple[int, float, float]:
    starts = episode_starts(d[alert_col])

    def related(ts: pd.Timestamp) -> bool:
        for _, f in failures.iterrows():
            if (
                f["failure_start"] - pd.Timedelta(hours=WARNING_HORIZON_HOURS)
                <= ts
                <= f["failure_end"]
            ):
                return True
        return False

    false_starts = [ts for ts in starts if not related(ts)]
    days = max((d.index.max() - d.index.min()).total_seconds() / 86400.0, 1e-9)
    return len(false_starts), len(false_starts) / days, days


def main() -> None:
    repo = find_repo_root()

    source = (
        repo
        / "data"
        / "gold"
        / "advanced_analytics"
        / "metropt_anomaly"
        / "metropt_anomaly_windows.parquet"
    )
    failure_path = (
        repo
        / "sources"
        / "step02-telemetry"
        / "data"
        / "bronze"
        / "metropt3"
        / "reference"
        / "failure_windows.csv"
    )
    out_dir = repo / "data" / "gold" / "advanced_analytics" / "metropt_anomaly"
    report_dir = repo / "reports" / "advanced_analytics"

    if not source.exists():
        raise FileNotFoundError(
            "Stage 12C output not found. Run run_stage12c_metropt_anomaly.py first."
        )

    d = pd.read_parquet(source)
    d["window_start"] = pd.to_datetime(d["window_start"])
    d = d.sort_values("window_start").set_index("window_start")

    failures = parse_failure_windows(failure_path)

    score = d["iforest_anomaly_score"].astype(float)

    # Only scores at least 24 hours old can enter the current threshold history.
    lagged = score.shift(LAG_BINS)

    adaptive_threshold = lagged.rolling(
        window=LOOKBACK_BINS,
        min_periods=MIN_HISTORY_BINS,
    ).quantile(ADAPTIVE_QUANTILE)

    d["adaptive_threshold"] = adaptive_threshold
    d["adaptive_raw_anomaly"] = (
        d["iforest_anomaly_score"] >= d["adaptive_threshold"]
    ) & d["adaptive_threshold"].notna()
    d["adaptive_alert"] = persistent_alert(d["adaptive_raw_anomaly"])

    # Holdout remains March onward, identical to Stage 12C.
    holdout = d.loc[d.index >= pd.Timestamp("2020-03-01")].copy()

    events = event_evaluation(holdout, failures, "adaptive_alert")
    false_count, false_per_day, holdout_days = false_alert_metrics(
        holdout, failures, "adaptive_alert"
    )

    detected = int(events["detected_within_24h_or_during"].sum()) if len(events) else 0
    early = int(events["detected_at_least_2h_early"].sum()) if len(events) else 0
    leads = events.loc[
        events["detected_within_24h_or_during"], "lead_time_hours"
    ] if len(events) else pd.Series(dtype=float)

    metrics = {
        "method": "causal_adaptive_isolation_forest_alerting",
        "model_retrained": False,
        "failure_labels_used_for_threshold_tuning": False,
        "adaptive_threshold": {
            "lookback_days": 7,
            "exclusion_lag_hours": 24,
            "minimum_history_days": 3,
            "quantile": ADAPTIVE_QUANTILE,
            "persistence_rule": f"{ALERT_REQUIRED_BINS}-of-{ALERT_WINDOW_BINS}",
        },
        "holdout": {
            "start": str(holdout.index.min()),
            "end": str(holdout.index.max()),
            "days": holdout_days,
        },
        "evaluation": {
            "failure_events": int(len(events)),
            "detected_events": detected,
            "detected_at_least_2h_early": early,
            "median_lead_time_hours": float(leads.median()) if len(leads) else None,
            "false_alert_episodes": int(false_count),
            "false_alert_episodes_per_day": float(false_per_day),
            "time_in_alert_pct": float(100 * holdout["adaptive_alert"].mean()),
            "raw_anomaly_pct": float(100 * holdout["adaptive_raw_anomaly"].mean()),
        },
        "acceptance_targets": {
            "failure_event_recall": "prefer 4/4; do not tune against labels to force it",
            "false_alert_episodes_per_day": "< 0.5 preferred",
            "time_in_alert_pct": "< 3% preferred",
            "lead_time": "retain operationally useful multi-hour warning",
        },
    }

    # Monthly diagnostic.
    monthly = (
        holdout.assign(month=holdout.index.to_period("M").astype(str))
        .groupby("month")
        .agg(
            windows=("iforest_anomaly_score", "size"),
            score_median=("iforest_anomaly_score", "median"),
            adaptive_threshold_median=("adaptive_threshold", "median"),
            raw_anomaly_pct=("adaptive_raw_anomaly", lambda x: 100 * x.mean()),
            alert_pct=("adaptive_alert", lambda x: 100 * x.mean()),
        )
        .reset_index()
    )

    # Save revised analytical outputs.
    cols = [
        "iforest_anomaly_score",
        "adaptive_threshold",
        "adaptive_raw_anomaly",
        "adaptive_alert",
        "in_failure",
        "in_warning_horizon",
        "failure_id",
    ]
    d[cols].reset_index().to_parquet(
        out_dir / "metropt_adaptive_anomaly_windows.parquet",
        index=False,
    )
    events.to_csv(
        out_dir / "metropt_adaptive_failure_event_evaluation.csv",
        index=False,
    )
    monthly.to_csv(
        out_dir / "metropt_adaptive_monthly_diagnostics.csv",
        index=False,
    )

    # Alert episodes.
    alerts = []
    for i, ts in enumerate(episode_starts(holdout["adaptive_alert"]), start=1):
        related_failure = None
        for _, f in failures.iterrows():
            if (
                f["failure_start"] - pd.Timedelta(hours=WARNING_HORIZON_HOURS)
                <= ts
                <= f["failure_end"]
            ):
                related_failure = f["failure_id"]
                break
        alerts.append({
            "alert_id": i,
            "alert_start": ts,
            "anomaly_score": float(holdout.loc[ts, "iforest_anomaly_score"]),
            "adaptive_threshold": float(holdout.loc[ts, "adaptive_threshold"]),
            "related_failure_id": related_failure,
            "is_failure_related": related_failure is not None,
        })

    pd.DataFrame(alerts).to_csv(
        out_dir / "metropt_adaptive_alert_episodes.csv",
        index=False,
    )

    with open(
        report_dir / "stage12c2_adaptive_alert_metrics.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(metrics, f, indent=2)

    print("=== Stage 12C.2 causal adaptive alerting ===")
    print(f"Holdout: {holdout.index.min()} -> {holdout.index.max()}")
    print("")
    print("=== Adaptive Isolation Forest result ===")
    print(f"Failure events detected: {detected}/{len(events)}")
    print(f"Detected >=2 h early: {early}/{len(events)}")
    print(
        "Median lead time (detected events): "
        f"{metrics['evaluation']['median_lead_time_hours']}"
    )
    print(f"False alert episodes/day: {false_per_day:.4f}")
    print(f"Time in alert: {metrics['evaluation']['time_in_alert_pct']:.4f}%")
    print(f"Raw anomaly windows: {metrics['evaluation']['raw_anomaly_pct']:.4f}%")

    print("\n=== Event detail ===")
    if len(events):
        print(events.to_string(index=False))

    print("\n=== Monthly diagnostics ===")
    print(monthly.to_string(index=False))

    print("\nOutputs written under:")
    print(out_dir.relative_to(repo))
    print(
        (report_dir / "stage12c2_adaptive_alert_metrics.json").relative_to(repo)
    )
    print("=== Stage 12C.2 complete ===")


if __name__ == "__main__":
    main()
