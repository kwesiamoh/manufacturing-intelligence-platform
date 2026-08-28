from __future__ import annotations

from pathlib import Path
import json
import itertools

import numpy as np
import pandas as pd

LOOKBACK_DAYS = 7
LAG_HOURS = 24
MIN_HISTORY_DAYS = 3
WARNING_HORIZON_HOURS = 24
TARGET_LEAD_HOURS = 2

# Small, pre-declared policy grid.
QUANTILES = [0.985, 0.990, 0.9925, 0.995]
PERSISTENCE = [(2, 3), (3, 4)]

MAX_FALSE_ALERTS_PER_DAY = 0.50
MAX_TIME_IN_ALERT_PCT = 3.00


def find_repo_root() -> Path:
    here = Path.cwd()
    for c in [here, *here.parents]:
        if (c / "sources").exists() and (c / "data").exists():
            return c
    raise FileNotFoundError("Run from repository root or a subdirectory.")


def parse_failures(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path)
    d.columns = [str(c).strip().lower().replace(" ", "_").replace("-", "_") for c in d.columns]

    starts = next((c for c in [
        "start", "start_time", "start_timestamp", "failure_start",
        "failure_start_time", "failure_start_timestamp"
    ] if c in d.columns), None)
    ends = next((c for c in [
        "end", "end_time", "end_timestamp", "failure_end",
        "failure_end_time", "failure_end_timestamp"
    ] if c in d.columns), None)
    ids = next((c for c in ["failure_id", "event_id", "id", "failure", "event"] if c in d.columns), None)

    if starts is None or ends is None:
        dt_cols = []
        for c in d.columns:
            p = pd.to_datetime(d[c], errors="coerce")
            if p.notna().mean() >= 0.8:
                dt_cols.append(c)
        if len(dt_cols) < 2:
            raise ValueError(f"Could not infer failure columns: {list(d.columns)}")
        starts, ends = dt_cols[:2]

    out = pd.DataFrame({
        "failure_start": pd.to_datetime(d[starts], errors="coerce"),
        "failure_end": pd.to_datetime(d[ends], errors="coerce"),
    }).dropna()
    out["failure_id"] = d.loc[out.index, ids].astype(str).values if ids else [str(i+1) for i in range(len(out))]
    return out.sort_values("failure_start").reset_index(drop=True)


def adaptive_threshold(score: pd.Series, q: float) -> pd.Series:
    bins_per_day = 24 * 12
    return (
        score.shift(LAG_HOURS * 12)
        .rolling(
            LOOKBACK_DAYS * bins_per_day,
            min_periods=MIN_HISTORY_DAYS * bins_per_day
        )
        .quantile(q)
    )


def persistent(raw: pd.Series, required: int, window: int) -> pd.Series:
    return (
        raw.astype("int8")
        .rolling(window, min_periods=window)
        .sum()
        .ge(required)
    )


def episode_starts(alert: pd.Series) -> pd.DatetimeIndex:
    return alert.index[alert & ~alert.shift(1, fill_value=False)]


def event_metrics(d: pd.DataFrame, failures: pd.DataFrame, alert_col: str) -> dict:
    detected = 0
    early = 0
    leads = []

    for _, f in failures.iterrows():
        ws = f.failure_start - pd.Timedelta(hours=WARNING_HORIZON_HOURS)
        hit = d.loc[(d.index >= ws) & (d.index <= f.failure_end) & d[alert_col]]
        if len(hit):
            detected += 1
            lead = (f.failure_start - hit.index[0]).total_seconds() / 3600.0
            leads.append(lead)
            if lead >= TARGET_LEAD_HOURS:
                early += 1

    return {
        "events": int(len(failures)),
        "detected": int(detected),
        "early_2h": int(early),
        "median_lead_h": float(np.median(leads)) if leads else None,
    }


def false_alert_metrics(d: pd.DataFrame, failures: pd.DataFrame, alert_col: str) -> tuple[int, float, float]:
    starts = episode_starts(d[alert_col])

    def related(ts):
        for _, f in failures.iterrows():
            if f.failure_start - pd.Timedelta(hours=WARNING_HORIZON_HOURS) <= ts <= f.failure_end:
                return True
        return False

    false_count = sum(not related(ts) for ts in starts)
    days = max((d.index.max() - d.index.min()).total_seconds()/86400.0, 1e-9)
    return false_count, false_count/days, 100.0*d[alert_col].mean()


def main():
    repo = find_repo_root()

    p = repo / "data" / "gold" / "advanced_analytics" / "metropt_anomaly" / "metropt_anomaly_windows.parquet"
    fpath = repo / "sources" / "metropt-telemetry" / "data" / "bronze" / "metropt3" / "reference" / "failure_windows.csv"
    outdir = repo / "data" / "gold" / "advanced_analytics" / "metropt_anomaly"
    reportdir = repo / "reports" / "advanced_analytics"
    reportdir.mkdir(parents=True, exist_ok=True)

    d = pd.read_parquet(p)
    d["window_start"] = pd.to_datetime(d["window_start"])
    d = d.sort_values("window_start").set_index("window_start")
    d = d.loc[d.index >= pd.Timestamp("2020-03-01")].copy()

    failures = parse_failures(fpath)
    if len(failures) < 4:
        raise ValueError(f"Expected at least four failure events, found {len(failures)}.")

    # Time-ordered event split.
    validation_failures = failures.iloc[:2].copy()
    test_failures = failures.iloc[2:4].copy()

    # Validation interval ends before failure 3 warning horizon starts.
    val_end = test_failures.iloc[0].failure_start - pd.Timedelta(hours=WARNING_HORIZON_HOURS)
    validation = d.loc[d.index < val_end].copy()
    test = d.loc[d.index >= val_end].copy()

    score = d["iforest_anomaly_score"].astype(float)

    rows = []
    policies = {}

    for q, (required, window) in itertools.product(QUANTILES, PERSISTENCE):
        t = adaptive_threshold(score, q)
        raw = (score >= t) & t.notna()
        alert = persistent(raw, required, window)

        name = f"q{q:.4f}_{required}of{window}"
        policies[name] = {"threshold": t, "raw": raw, "alert": alert}

        tmp = d.copy()
        tmp["candidate_alert"] = alert

        val_tmp = tmp.loc[validation.index]
        em = event_metrics(val_tmp, validation_failures, "candidate_alert")
        false_n, false_day, alert_pct = false_alert_metrics(
            val_tmp, validation_failures, "candidate_alert"
        )

        rows.append({
            "policy": name,
            "quantile": q,
            "required": required,
            "window": window,
            "validation_events": em["events"],
            "validation_detected": em["detected"],
            "validation_early_2h": em["early_2h"],
            "validation_median_lead_h": em["median_lead_h"],
            "validation_false_alerts": false_n,
            "validation_false_alerts_per_day": false_day,
            "validation_time_in_alert_pct": alert_pct,
            "within_alert_budget": (
                false_day <= MAX_FALSE_ALERTS_PER_DAY
                and alert_pct <= MAX_TIME_IN_ALERT_PCT
            ),
        })

    results = pd.DataFrame(rows)

    eligible = results.loc[results["within_alert_budget"]].copy()
    if eligible.empty:
        # If none meets budget, choose lowest false burden first.
        ranked = results.sort_values(
            ["validation_false_alerts_per_day", "validation_time_in_alert_pct",
             "validation_early_2h", "validation_detected"],
            ascending=[True, True, False, False]
        )
    else:
        # Policy selection uses validation events only, after satisfying the
        # operational alert-budget constraint.
        ranked = eligible.sort_values(
            ["validation_early_2h", "validation_detected",
             "validation_false_alerts_per_day", "validation_time_in_alert_pct"],
            ascending=[False, False, True, True]
        )

    winner = ranked.iloc[0]
    winner_name = winner["policy"]
    chosen = policies[winner_name]

    final = d.copy()
    final["selected_threshold"] = chosen["threshold"]
    final["selected_raw_anomaly"] = chosen["raw"]
    final["selected_alert"] = chosen["alert"]

    # Test uses only events 3 and 4 and is not involved in policy selection.
    test_frame = final.loc[test.index]
    test_em = event_metrics(test_frame, test_failures, "selected_alert")
    test_false_n, test_false_day, test_alert_pct = false_alert_metrics(
        test_frame, test_failures, "selected_alert"
    )

    # Full-period metrics are descriptive only after policy is frozen.
    full_em = event_metrics(final, failures.iloc[:4], "selected_alert")
    full_false_n, full_false_day, full_alert_pct = false_alert_metrics(
        final, failures.iloc[:4], "selected_alert"
    )

    report = {
        "selection_protocol": {
            "policy_grid_declared_in_advance": True,
            "validation_events": validation_failures.failure_id.tolist(),
            "test_events": test_failures.failure_id.tolist(),
            "alert_budget": {
                "max_false_alert_episodes_per_day": MAX_FALSE_ALERTS_PER_DAY,
                "max_time_in_alert_pct": MAX_TIME_IN_ALERT_PCT,
            },
        },
        "selected_policy": {
            "name": winner_name,
            "quantile": float(winner["quantile"]),
            "persistence": f"{int(winner['required'])}-of-{int(winner['window'])}",
            "lookback_days": LOOKBACK_DAYS,
            "lag_hours": LAG_HOURS,
        },
        "validation": {
            "events": int(winner["validation_events"]),
            "detected": int(winner["validation_detected"]),
            "early_2h": int(winner["validation_early_2h"]),
            "false_alerts_per_day": float(winner["validation_false_alerts_per_day"]),
            "time_in_alert_pct": float(winner["validation_time_in_alert_pct"]),
        },
        "final_time_ordered_test": {
            **test_em,
            "false_alerts": int(test_false_n),
            "false_alerts_per_day": float(test_false_day),
            "time_in_alert_pct": float(test_alert_pct),
        },
        "full_period_descriptive": {
            **full_em,
            "false_alerts": int(full_false_n),
            "false_alerts_per_day": float(full_false_day),
            "time_in_alert_pct": float(full_alert_pct),
        },
        "limitation": (
            "Only four independent failure events are available. "
            "Events 1-2 are used for policy validation and events 3-4 for the "
            "final time-ordered test; all event-level results should therefore "
            "be interpreted as small-sample evidence."
        )
    }

    results.sort_values(
        ["within_alert_budget", "validation_early_2h", "validation_detected",
         "validation_false_alerts_per_day"],
        ascending=[False, False, False, True]
    ).to_csv(outdir / "metropt_alert_policy_validation_grid.csv", index=False)

    final[[
        "iforest_anomaly_score",
        "selected_threshold",
        "selected_raw_anomaly",
        "selected_alert",
        "in_failure",
        "in_warning_horizon",
        "failure_id",
    ]].reset_index().to_parquet(
        outdir / "metropt_selected_alert_policy_windows.parquet",
        index=False
    )

    with open(reportdir / "metropt_alert_policy_metrics.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("=== MetroPT alert-policy selection alert policy selection ===")
    print(f"Validation events: {', '.join(validation_failures.failure_id.astype(str))}")
    print(f"Final test events: {', '.join(test_failures.failure_id.astype(str))}")
    print("")
    print("=== Candidate policies ===")
    print(results.to_string(index=False))
    print("")
    print("=== Selected policy ===")
    print(f"Policy: {winner_name}")
    print(f"Quantile: {winner['quantile']}")
    print(f"Persistence: {int(winner['required'])}-of-{int(winner['window'])}")
    print("")
    print("=== Final time-ordered test: failures 3 and 4 ===")
    print(f"Detected: {test_em['detected']}/{test_em['events']}")
    print(f"Detected >=2 h early: {test_em['early_2h']}/{test_em['events']}")
    print(f"Median lead time: {test_em['median_lead_h']}")
    print(f"False alert episodes/day: {test_false_day:.4f}")
    print(f"Time in alert: {test_alert_pct:.4f}%")
    print("")
    print("=== Full-period descriptive result ===")
    print(f"Detected: {full_em['detected']}/{full_em['events']}")
    print(f"Detected >=2 h early: {full_em['early_2h']}/{full_em['events']}")
    print(f"False alert episodes/day: {full_false_day:.4f}")
    print(f"Time in alert: {full_alert_pct:.4f}%")
    print("=== MetroPT alert-policy selection complete ===")


if __name__ == "__main__":
    main()
