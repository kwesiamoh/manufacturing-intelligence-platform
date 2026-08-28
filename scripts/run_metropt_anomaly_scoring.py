from __future__ import annotations

import json
import math
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd
import pyarrow.dataset as ds

from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, precision_recall_curve
from sklearn.preprocessing import RobustScaler

warnings.filterwarnings("ignore", category=RuntimeWarning)

# ---------------------------------------------------------------------------
# MetroPT anomaly scoring — MetroPT-3 causal anomaly detection
#
# Design:
#   raw cadence           : ~10 s
#   analytical bin        : 5 min
#   causal context        : trailing 60 min
#   training              : first 70% of first calendar month, normal only
#   calibration           : final 30% of first calendar month, normal only
#   holdout               : all later months
#   model                 : Isolation Forest
#   threshold             : 99.5th percentile of calibration anomaly scores
#   persistent alert      : >=3 anomalous bins in trailing 4 bins
#   event warning horizon : 24 h before failure start through failure end
#   minimum useful lead   : 2 h
#
# The pipeline never uses future sensor values to build features or alerts.
# Failure windows are used only to exclude contaminated training/calibration
# periods and to evaluate the held-out anomaly detector.
# ---------------------------------------------------------------------------

ANALOG = [
    "tp2",
    "tp3",
    "h1",
    "dv_pressure",
    "reservoirs",
    "oil_temperature",
    "motor_current",
]

DIGITAL = [
    "comp",
    "dv_eletric",
    "towers",
    "mpg",
    "lps",
    "pressure_switch",
    "oil_level",
    "caudal_impulses",
]

BIN_FREQ = "5min"
CONTEXT_BINS = 12
EXPECTED_RAW_PER_BIN = 30
MIN_BIN_COVERAGE = 0.80
CALIBRATION_QUANTILE = 0.995
ALERT_WINDOW_BINS = 4
ALERT_REQUIRED_BINS = 3
WARNING_HORIZON_HOURS = 24
TARGET_LEAD_HOURS = 2
EXCLUSION_BUFFER_HOURS = 24
RANDOM_STATE = 42


@dataclass
class FailureWindow:
    failure_id: str
    start: pd.Timestamp
    end: pd.Timestamp


def find_repo_root() -> Path:
    here = Path.cwd()
    for candidate in [here, *here.parents]:
        if (candidate / "sources").exists():
            return candidate
    raise FileNotFoundError(
        "Could not identify repository root. Run this script from the repository "
        "or one of its subdirectories."
    )


def locate_metropt_silver(repo: Path) -> Path:
    expected = repo / "sources" / "metropt-telemetry" / "data" / "silver" / "telemetry" / "metropt3"
    if expected.exists():
        return expected

    candidates = [
        p for p in (repo / "sources").rglob("*")
        if p.is_dir()
        and "metropt" in p.name.lower()
        and any(p.glob("*.parquet"))
    ]
    if not candidates:
        raise FileNotFoundError("MetroPT Silver Parquet directory was not found.")
    return sorted(candidates, key=lambda p: len(p.parts))[0]


def locate_failure_windows(repo: Path) -> Path:
    expected = (
        repo
        / "sources"
        / "metropt-telemetry"
        / "data"
        / "bronze"
        / "metropt3"
        / "reference"
        / "failure_windows.csv"
    )
    if expected.exists():
        return expected

    matches = list((repo / "sources").rglob("failure_windows.csv"))
    if not matches:
        raise FileNotFoundError("failure_windows.csv was not found under sources/.")
    return matches[0]


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [
        str(c).strip().lower().replace(" ", "_").replace("-", "_")
        for c in out.columns
    ]
    return out


def parse_failure_windows(path: Path) -> list[FailureWindow]:
    raw = normalize_column_names(pd.read_csv(path))

    def first_matching(names: Iterable[str]) -> str | None:
        for n in names:
            if n in raw.columns:
                return n
        return None

    start_col = first_matching([
        "start", "start_time", "start_timestamp", "failure_start",
        "failure_start_time", "failure_start_timestamp", "begin", "begin_time",
    ])
    end_col = first_matching([
        "end", "end_time", "end_timestamp", "failure_end",
        "failure_end_time", "failure_end_timestamp", "finish", "finish_time",
    ])
    id_col = first_matching([
        "failure_id", "event_id", "id", "failure", "event", "description",
    ])

    if start_col is None or end_col is None:
        datetime_like = []
        for c in raw.columns:
            parsed = pd.to_datetime(raw[c], errors="coerce")
            if parsed.notna().mean() >= 0.80:
                datetime_like.append(c)
        if len(datetime_like) >= 2:
            start_col, end_col = datetime_like[:2]
        else:
            raise ValueError(
                "Could not infer failure start/end columns. "
                f"Columns found: {list(raw.columns)}"
            )

    starts = pd.to_datetime(raw[start_col], errors="coerce")
    ends = pd.to_datetime(raw[end_col], errors="coerce")

    windows: list[FailureWindow] = []
    for i, (s, e) in enumerate(zip(starts, ends), start=1):
        if pd.isna(s) or pd.isna(e):
            continue
        if e < s:
            s, e = e, s
        fid = str(raw.iloc[i - 1][id_col]) if id_col else f"failure_{i:02d}"
        windows.append(FailureWindow(fid, pd.Timestamp(s), pd.Timestamp(e)))

    if not windows:
        raise ValueError("No valid failure windows were parsed.")
    return windows


def read_metropt(path: Path) -> pd.DataFrame:
    dataset = ds.dataset(str(path), format="parquet")
    available = {c.lower(): c for c in dataset.schema.names}

    time_candidates = ["timestamp", "datetime", "date_time", "time"]
    time_source = next((available[c] for c in time_candidates if c in available), None)
    if time_source is None:
        raise ValueError(
            f"No timestamp column found. Available columns: {dataset.schema.names}"
        )

    requested_lower = [time_source.lower(), *ANALOG, *DIGITAL]
    missing = [c for c in requested_lower if c not in available]
    if missing:
        raise ValueError(
            "MetroPT Silver schema is missing expected columns: "
            + ", ".join(missing)
        )

    source_cols = [available[c] for c in requested_lower]
    table = dataset.to_table(columns=source_cols)
    df = table.to_pandas()
    df = normalize_column_names(df)

    if time_source.lower() != "timestamp":
        df = df.rename(columns={time_source.lower(): "timestamp"})

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp").drop_duplicates("timestamp")

    for c in ANALOG + DIGITAL:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


def make_5min_features(raw: pd.DataFrame) -> pd.DataFrame:
    x = raw.set_index("timestamp").sort_index()

    counts = x[ANALOG[0]].resample(BIN_FREQ).count()
    out = pd.DataFrame(index=counts.index)
    out["raw_samples"] = counts
    out["coverage_ratio"] = counts / EXPECTED_RAW_PER_BIN

    # Continuous channels
    for c in ANALOG:
        r = x[c].resample(BIN_FREQ)
        out[f"{c}__mean"] = r.mean()
        out[f"{c}__std"] = r.std(ddof=0)
        out[f"{c}__min"] = r.min()
        out[f"{c}__max"] = r.max()
        out[f"{c}__last"] = r.last()
        out[f"{c}__range"] = out[f"{c}__max"] - out[f"{c}__min"]

        # Causal within-bin behavior.
        diff_abs = x[c].diff().abs().resample(BIN_FREQ).mean()
        first = r.first()
        last = r.last()
        out[f"{c}__absdiff_mean"] = diff_abs
        out[f"{c}__delta"] = last - first

    # Discrete/state channels.
    for c in DIGITAL:
        r = x[c].resample(BIN_FREQ)
        out[f"{c}__active_frac"] = r.mean()
        out[f"{c}__last"] = r.last()

        transitions = (
            x[c]
            .ne(x[c].shift(1))
            .astype("int8")
            .resample(BIN_FREQ)
            .sum()
        )
        out[f"{c}__transitions"] = transitions

    out["valid_bin"] = out["coverage_ratio"] >= MIN_BIN_COVERAGE
    return out


def add_causal_context(features: pd.DataFrame) -> pd.DataFrame:
    out = features.copy()

    # 60-minute context from past/current 5-minute bins only.
    for c in ANALOG:
        mean_col = f"{c}__mean"
        std_col = f"{c}__std"

        roll_mean = out[mean_col].rolling(CONTEXT_BINS, min_periods=6).mean()
        roll_std = out[mean_col].rolling(CONTEXT_BINS, min_periods=6).std(ddof=0)

        out[f"{c}__mean_60m"] = roll_mean
        out[f"{c}__std_60m"] = roll_std
        out[f"{c}__deviation_60m"] = out[mean_col] - roll_mean
        out[f"{c}__within_std_60m"] = (
            out[std_col].rolling(CONTEXT_BINS, min_periods=6).mean()
        )

    for c in DIGITAL:
        active_col = f"{c}__active_frac"
        out[f"{c}__active_frac_60m"] = (
            out[active_col].rolling(CONTEXT_BINS, min_periods=6).mean()
        )

    return out


def mark_failure_context(
    index: pd.DatetimeIndex,
    failures: list[FailureWindow],
) -> pd.DataFrame:
    labels = pd.DataFrame(index=index)
    labels["in_failure"] = False
    labels["in_warning_horizon"] = False
    labels["training_exclusion"] = False
    labels["failure_id"] = pd.Series(index=index, dtype="object")

    warning_delta = pd.Timedelta(hours=WARNING_HORIZON_HOURS)
    exclusion_delta = pd.Timedelta(hours=EXCLUSION_BUFFER_HOURS)

    for f in failures:
        in_failure = (index >= f.start) & (index <= f.end)
        in_warning = (index >= f.start - warning_delta) & (index <= f.end)
        in_exclusion = (index >= f.start - exclusion_delta) & (index <= f.end + exclusion_delta)

        labels.loc[in_failure, "in_failure"] = True
        labels.loc[in_warning, "in_warning_horizon"] = True
        labels.loc[in_exclusion, "training_exclusion"] = True
        labels.loc[in_warning, "failure_id"] = f.failure_id

    return labels


def choose_split(index: pd.DatetimeIndex) -> tuple[pd.Timestamp, pd.Timestamp]:
    start = index.min()
    first_month_start = start.to_period("M").start_time
    next_month_start = (first_month_start + pd.offsets.MonthBegin(1))

    first_month_index = index[(index >= start) & (index < next_month_start)]
    if len(first_month_index) < 100:
        raise ValueError("Not enough observations in first calendar month for train/calibration split.")

    split_pos = int(len(first_month_index) * 0.70)
    train_end = first_month_index[split_pos]
    holdout_start = next_month_start
    return train_end, holdout_start


def model_feature_columns(df: pd.DataFrame) -> list[str]:
    excluded = {
        "raw_samples", "coverage_ratio", "valid_bin",
        "in_failure", "in_warning_horizon", "training_exclusion",
        "failure_id",
    }
    return [
        c for c in df.columns
        if c not in excluded and pd.api.types.is_numeric_dtype(df[c])
    ]


def make_alerts(raw_anomaly: pd.Series) -> pd.Series:
    # Causal persistence: current window alerts only when at least 3 of the
    # current/trailing 4 raw anomaly flags are positive.
    return (
        raw_anomaly.astype(int)
        .rolling(ALERT_WINDOW_BINS, min_periods=ALERT_WINDOW_BINS)
        .sum()
        .ge(ALERT_REQUIRED_BINS)
    )


def alert_episode_starts(alert: pd.Series) -> pd.DatetimeIndex:
    starts = alert & ~alert.shift(1, fill_value=False)
    return alert.index[starts]


def evaluate_events(
    holdout: pd.DataFrame,
    failures: list[FailureWindow],
    alert_col: str,
) -> pd.DataFrame:
    records = []
    for f in failures:
        if f.end < holdout.index.min() or f.start > holdout.index.max():
            continue

        warning_start = f.start - pd.Timedelta(hours=WARNING_HORIZON_HOURS)
        window = holdout.loc[
            (holdout.index >= warning_start)
            & (holdout.index <= f.end)
            & holdout[alert_col]
        ]

        if len(window):
            first_alert = window.index[0]
            lead_hours = (f.start - first_alert).total_seconds() / 3600
            detected = True
            early_2h = first_alert <= f.start - pd.Timedelta(hours=TARGET_LEAD_HOURS)
        else:
            first_alert = pd.NaT
            lead_hours = np.nan
            detected = False
            early_2h = False

        records.append({
            "failure_id": f.failure_id,
            "failure_start": f.start,
            "failure_end": f.end,
            "detected_within_24h_or_during": detected,
            "detected_at_least_2h_early": early_2h,
            "first_alert_timestamp": first_alert,
            "lead_time_hours": lead_hours,
        })

    return pd.DataFrame(records)


def false_alerts_per_day(
    holdout: pd.DataFrame,
    failures: list[FailureWindow],
    alert_col: str,
) -> tuple[int, float, float]:
    starts = alert_episode_starts(holdout[alert_col])

    def is_failure_related(ts: pd.Timestamp) -> bool:
        for f in failures:
            if (
                f.start - pd.Timedelta(hours=WARNING_HORIZON_HOURS)
                <= ts
                <= f.end
            ):
                return True
        return False

    false_starts = [ts for ts in starts if not is_failure_related(ts)]
    days = max(
        (holdout.index.max() - holdout.index.min()).total_seconds() / 86400,
        1e-9,
    )
    return len(false_starts), len(false_starts) / days, days


def robust_z_baseline(
    train: pd.DataFrame,
    calibration: pd.DataFrame,
    full: pd.DataFrame,
    feature_cols: list[str],
) -> tuple[pd.Series, float]:
    med = train[feature_cols].median()
    q1 = train[feature_cols].quantile(0.25)
    q3 = train[feature_cols].quantile(0.75)
    iqr = (q3 - q1).replace(0, np.nan)

    def score(df: pd.DataFrame) -> pd.Series:
        z = ((df[feature_cols] - med) / iqr).abs()
        return z.max(axis=1, skipna=True)

    cal_score = score(calibration)
    threshold = float(cal_score.quantile(CALIBRATION_QUANTILE))
    return score(full), threshold


def main() -> None:
    repo = find_repo_root()
    silver = locate_metropt_silver(repo)
    failures_path = locate_failure_windows(repo)

    out_dir = repo / "data" / "gold" / "advanced_analytics" / "metropt_anomaly"
    report_dir = repo / "reports" / "advanced_analytics"
    model_dir = repo / "models" / "advanced_analytics" / "metropt"
    for p in [out_dir, report_dir, model_dir]:
        p.mkdir(parents=True, exist_ok=True)

    print("=== MetroPT anomaly scoring MetroPT anomaly detection ===")
    print(f"Silver source: {silver.relative_to(repo)}")
    print(f"Failure reference: {failures_path.relative_to(repo)}")

    failures = parse_failure_windows(failures_path)
    print(f"Failure windows parsed: {len(failures)}")

    raw = read_metropt(silver)
    print(f"Raw observations loaded: {len(raw):,}")
    print(f"Raw coverage: {raw['timestamp'].min()} -> {raw['timestamp'].max()}")

    features = add_causal_context(make_5min_features(raw))
    labels = mark_failure_context(features.index, failures)
    frame = features.join(labels)

    feature_cols = model_feature_columns(frame)
    frame = frame.loc[frame["valid_bin"]].copy()
    frame = frame.dropna(subset=feature_cols)

    train_end, holdout_start = choose_split(frame.index)
    first_ts = frame.index.min()

    train_mask = (
        (frame.index >= first_ts)
        & (frame.index < train_end)
        & (~frame["training_exclusion"])
    )
    calibration_mask = (
        (frame.index >= train_end)
        & (frame.index < holdout_start)
        & (~frame["training_exclusion"])
    )
    holdout_mask = frame.index >= holdout_start

    train = frame.loc[train_mask].copy()
    calibration = frame.loc[calibration_mask].copy()
    holdout = frame.loc[holdout_mask].copy()

    if len(train) < 500 or len(calibration) < 100 or len(holdout) < 100:
        raise ValueError(
            "Insufficient data after causal feature construction and failure exclusions: "
            f"train={len(train)}, calibration={len(calibration)}, holdout={len(holdout)}"
        )

    print(f"Model features: {len(feature_cols)}")
    print(f"Training windows: {len(train):,}")
    print(f"Calibration windows: {len(calibration):,}")
    print(f"Holdout windows: {len(holdout):,}")
    print(f"Train end: {train_end}")
    print(f"Holdout start: {holdout_start}")

    scaler = RobustScaler()
    X_train = scaler.fit_transform(train[feature_cols])
    X_cal = scaler.transform(calibration[feature_cols])
    X_all = scaler.transform(frame[feature_cols])

    model = IsolationForest(
        n_estimators=300,
        max_samples="auto",
        contamination="auto",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_train)

    # sklearn decision_function is higher for normal; invert so higher = more anomalous.
    cal_scores = -model.decision_function(X_cal)
    all_scores = -model.decision_function(X_all)
    threshold = float(np.quantile(cal_scores, CALIBRATION_QUANTILE))

    frame["iforest_anomaly_score"] = all_scores
    frame["iforest_raw_anomaly"] = frame["iforest_anomaly_score"] >= threshold
    frame["iforest_alert"] = make_alerts(frame["iforest_raw_anomaly"])

    # Transparent statistical reference baseline.
    rz_score, rz_threshold = robust_z_baseline(
        train, calibration, frame, feature_cols
    )
    frame["robust_z_score"] = rz_score
    frame["robust_z_raw_anomaly"] = frame["robust_z_score"] >= rz_threshold
    frame["robust_z_alert"] = make_alerts(frame["robust_z_raw_anomaly"])

    holdout = frame.loc[holdout_mask].copy()

    # Event-level evaluation.
    if_events = evaluate_events(holdout, failures, "iforest_alert")
    rz_events = evaluate_events(holdout, failures, "robust_z_alert")

    if_false_count, if_false_per_day, holdout_days = false_alerts_per_day(
        holdout, failures, "iforest_alert"
    )
    rz_false_count, rz_false_per_day, _ = false_alerts_per_day(
        holdout, failures, "robust_z_alert"
    )

    # Secondary window-level PR-AUC.
    y_true = holdout["in_warning_horizon"].astype(int).to_numpy()
    if len(np.unique(y_true)) > 1:
        if_pr_auc = float(
            average_precision_score(y_true, holdout["iforest_anomaly_score"])
        )
        rz_pr_auc = float(
            average_precision_score(y_true, holdout["robust_z_score"])
        )
    else:
        if_pr_auc = None
        rz_pr_auc = None

    def event_summary(events: pd.DataFrame) -> dict:
        if events.empty:
            return {
                "evaluated_failure_events": 0,
                "detected_events": 0,
                "detected_at_least_2h_early": 0,
                "median_lead_time_hours": None,
            }
        detected_leads = events.loc[
            events["detected_within_24h_or_during"], "lead_time_hours"
        ]
        return {
            "evaluated_failure_events": int(len(events)),
            "detected_events": int(events["detected_within_24h_or_during"].sum()),
            "detected_at_least_2h_early": int(events["detected_at_least_2h_early"].sum()),
            "median_lead_time_hours": (
                float(detected_leads.median()) if len(detected_leads) else None
            ),
        }

    metrics = {
        "source": {
            "dataset": "MetroPT-3",
            "is_real_data": True,
            "silver_path": str(silver.relative_to(repo)),
            "failure_reference_path": str(failures_path.relative_to(repo)),
            "raw_rows": int(len(raw)),
            "raw_start": str(raw["timestamp"].min()),
            "raw_end": str(raw["timestamp"].max()),
        },
        "design": {
            "bin_frequency": BIN_FREQ,
            "context_minutes": CONTEXT_BINS * 5,
            "minimum_bin_coverage": MIN_BIN_COVERAGE,
            "training_scheme": "first 70% of first calendar month, failure-buffer excluded",
            "calibration_scheme": "last 30% of first calendar month, failure-buffer excluded",
            "holdout_scheme": "all later calendar months",
            "calibration_quantile": CALIBRATION_QUANTILE,
            "persistent_alert_rule": f"{ALERT_REQUIRED_BINS}-of-{ALERT_WINDOW_BINS}",
            "warning_horizon_hours": WARNING_HORIZON_HOURS,
            "target_minimum_lead_hours": TARGET_LEAD_HOURS,
            "feature_count": len(feature_cols),
        },
        "split": {
            "train_windows": int(len(train)),
            "calibration_windows": int(len(calibration)),
            "holdout_windows": int(len(holdout)),
            "train_end": str(train_end),
            "holdout_start": str(holdout_start),
            "holdout_days": holdout_days,
        },
        "isolation_forest": {
            "threshold": threshold,
            **event_summary(if_events),
            "false_alert_episodes": int(if_false_count),
            "false_alert_episodes_per_day": float(if_false_per_day),
            "time_in_alert_pct": float(100 * holdout["iforest_alert"].mean()),
            "window_pr_auc": if_pr_auc,
        },
        "robust_z_baseline": {
            "threshold": float(rz_threshold),
            **event_summary(rz_events),
            "false_alert_episodes": int(rz_false_count),
            "false_alert_episodes_per_day": float(rz_false_per_day),
            "time_in_alert_pct": float(100 * holdout["robust_z_alert"].mean()),
            "window_pr_auc": rz_pr_auc,
        },
        "interpretation_note": (
            "Failure-event metrics are primary. Window-level PR-AUC is secondary. "
            "Known failure windows are never used to tune the Isolation Forest threshold."
        ),
    }

    # Persist compact analytical outputs.
    output_cols = [
        "raw_samples", "coverage_ratio",
        "iforest_anomaly_score", "iforest_raw_anomaly", "iforest_alert",
        "robust_z_score", "robust_z_raw_anomaly", "robust_z_alert",
        "in_failure", "in_warning_horizon", "failure_id",
    ]
    windows_out = frame[output_cols].copy()
    windows_out.index.name = "window_start"
    windows_out.reset_index().to_parquet(
        out_dir / "metropt_anomaly_windows.parquet", index=False
    )

    event_out = if_events.copy()
    event_out.insert(0, "model", "isolation_forest")
    rz_event_out = rz_events.copy()
    rz_event_out.insert(0, "model", "robust_z_baseline")
    pd.concat([event_out, rz_event_out], ignore_index=True).to_csv(
        out_dir / "metropt_failure_event_evaluation.csv", index=False
    )

    # Alert episode table for Power BI / review.
    alert_starts = alert_episode_starts(holdout["iforest_alert"])
    alerts = []
    for i, ts in enumerate(alert_starts, start=1):
        row = holdout.loc[ts]
        related_failure = None
        for f in failures:
            if (
                f.start - pd.Timedelta(hours=WARNING_HORIZON_HOURS)
                <= ts
                <= f.end
            ):
                related_failure = f.failure_id
                break
        alerts.append({
            "alert_id": i,
            "alert_start": ts,
            "anomaly_score": float(row["iforest_anomaly_score"]),
            "related_failure_id": related_failure,
            "is_failure_related": related_failure is not None,
        })
    pd.DataFrame(alerts).to_csv(
        out_dir / "metropt_alert_episodes.csv", index=False
    )

    with open(report_dir / "metropt_anomaly_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    with open(report_dir / "metropt_feature_columns.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(feature_cols))

    joblib.dump(scaler, model_dir / "robust_scaler.joblib")
    joblib.dump(model, model_dir / "isolation_forest.joblib")

    print("\n=== Isolation Forest holdout result ===")
    s = metrics["isolation_forest"]
    print(
        f"Failure events detected: {s['detected_events']}/"
        f"{s['evaluated_failure_events']}"
    )
    print(
        f"Detected >= {TARGET_LEAD_HOURS} h early: "
        f"{s['detected_at_least_2h_early']}/"
        f"{s['evaluated_failure_events']}"
    )
    print(f"False alert episodes/day: {s['false_alert_episodes_per_day']:.4f}")
    print(f"Median lead time (detected events): {s['median_lead_time_hours']}")
    print(f"Time in alert: {s['time_in_alert_pct']:.4f}%")
    print(f"Window PR-AUC: {s['window_pr_auc']}")

    print("\n=== Robust-z reference baseline ===")
    s = metrics["robust_z_baseline"]
    print(
        f"Failure events detected: {s['detected_events']}/"
        f"{s['evaluated_failure_events']}"
    )
    print(f"False alert episodes/day: {s['false_alert_episodes_per_day']:.4f}")
    print(f"Time in alert: {s['time_in_alert_pct']:.4f}%")
    print(f"Window PR-AUC: {s['window_pr_auc']}")

    print("\nOutputs:")
    print(f"  {out_dir.relative_to(repo)}")
    print(f"  {report_dir.relative_to(repo) / 'metropt_anomaly_metrics.json'}")
    print(f"  {model_dir.relative_to(repo)}")
    print("=== MetroPT anomaly scoring complete ===")


if __name__ == "__main__":
    main()
