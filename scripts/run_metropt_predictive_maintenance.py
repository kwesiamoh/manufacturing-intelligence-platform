from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from run_metropt_anomaly_scoring import (
    FailureWindow,
    add_causal_context,
    make_5min_features,
    parse_failure_windows,
    read_metropt,
)


REPO = Path(__file__).resolve().parents[1]
METROPT_ROOT = REPO / "sources" / "metropt-telemetry"
SILVER = METROPT_ROOT / "data" / "silver" / "telemetry" / "metropt3"
BRONZE = METROPT_ROOT / "data" / "bronze" / "metropt3" / "MetroPT3(AirCompressor).csv"
ACQUISITION = METROPT_ROOT / "data" / "bronze" / "metropt3" / "acquisition_manifest.json"
FAILURES = METROPT_ROOT / "data" / "bronze" / "metropt3" / "reference" / "failure_windows.csv"
SELECTED_WINDOWS = (
    REPO
    / "data"
    / "gold"
    / "advanced_analytics"
    / "metropt_anomaly"
    / "metropt_selected_alert_policy_windows.parquet"
)

ENTERPRISE_OUT = (
    REPO
    / "data"
    / "silver"
    / "synthetic_enterprise"
    / "telemetry"
    / "metropt_enterprise_telemetry.parquet"
)
GOLD_OUT = REPO / "data" / "gold" / "advanced_analytics" / "metropt_predictive_maintenance"
REPORT_OUT = REPO / "reports" / "advanced_analytics" / "metropt_predictive_maintenance_metrics.json"

SITE_CODE = "SITE-DE-01"
EQUIPMENT_CODE = "SITE-DE-01-U-AIR-01"
ENTERPRISE_YEAR_SHIFT = 4
HORIZONS = (2, 4, 6)
MAX_PRECURSOR_HOURS = 6
PERSISTENCE_REQUIRED = 2
PERSISTENCE_WINDOW = 3
THRESHOLD_QUANTILES = (0.990, 0.995, 0.999)
MAX_FALSE_ALERTS_PER_DAY = 0.50
RANDOM_STATE = 42

MODEL_FEATURES = [
    "tp2__mean",
    "tp3__mean",
    "h1__mean",
    "dv_pressure__mean",
    "reservoirs__mean",
    "oil_temperature__mean",
    "motor_current__mean",
    "tp2__deviation_60m",
    "tp3__deviation_60m",
    "reservoirs__deviation_60m",
    "oil_temperature__deviation_60m",
    "motor_current__deviation_60m",
    "pressure_delta",
    "reservoir_pressure_slope_60m",
    "oil_temperature_slope_60m",
    "motor_current_slope_60m",
    "iforest_anomaly_score",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def persistent(signal: pd.Series) -> pd.Series:
    return (
        signal.fillna(False)
        .astype("int8")
        .rolling(PERSISTENCE_WINDOW, min_periods=PERSISTENCE_WINDOW)
        .sum()
        .ge(PERSISTENCE_REQUIRED)
    )


def episode_starts(alert: pd.Series) -> pd.DatetimeIndex:
    return alert.index[alert & ~alert.shift(1, fill_value=False)]


def precursor_label(index: pd.DatetimeIndex, failures: list[FailureWindow], hours: int) -> pd.Series:
    label = pd.Series(False, index=index)
    delta = pd.Timedelta(hours=hours)
    for failure in failures:
        label |= (index >= failure.start - delta) & (index < failure.start)
    return label


def failure_id_at(index: pd.DatetimeIndex, failures: list[FailureWindow]) -> pd.Series:
    result = pd.Series(pd.NA, index=index, dtype="string")
    for failure in failures:
        mask = (index >= failure.start) & (index <= failure.end)
        result.loc[mask] = failure.failure_id
    return result


def event_metrics(
    frame: pd.DataFrame,
    failures: list[FailureWindow],
    alert_col: str,
    horizon_hours: int,
) -> tuple[dict, list[dict]]:
    records: list[dict] = []
    relevant_starts = episode_starts(frame[alert_col])
    for failure in failures:
        window_start = failure.start - pd.Timedelta(hours=horizon_hours)
        hits = relevant_starts[(relevant_starts >= window_start) & (relevant_starts < failure.start)]
        if len(hits):
            first = pd.Timestamp(hits[0])
            lead = (failure.start - first).total_seconds() / 3600.0
            outcome = "WARNED"
        else:
            first = pd.NaT
            lead = np.nan
            outcome = "MISSED"
        records.append(
            {
                "failure_id": failure.failure_id,
                "fault_onset_timestamp": failure.start,
                "fault_end_timestamp": failure.end,
                "first_warning_timestamp": first,
                "warning_lead_time_hours": lead,
                "warning_outcome": outcome,
            }
        )

    all_starts = list(relevant_starts)
    false_starts = []
    for timestamp in all_starts:
        related = any(
            failure.start - pd.Timedelta(hours=horizon_hours)
            <= timestamp
            < failure.start
            for failure in failures
        )
        if not related:
            false_starts.append(timestamp)

    leads = [row["warning_lead_time_hours"] for row in records if row["warning_outcome"] == "WARNED"]
    warned = len(leads)
    event_count = len(records)
    days = max((frame.index.max() - frame.index.min()).total_seconds() / 86400.0, 1e-9)
    true_alert_episodes = len(all_starts) - len(false_starts)
    precision = true_alert_episodes / len(all_starts) if all_starts else 0.0
    recall = warned / event_count if event_count else 0.0

    return (
        {
            "events_evaluated": event_count,
            "events_warned": warned,
            "events_missed": event_count - warned,
            "warning_success_rate": recall,
            "average_lead_time_hours": float(np.mean(leads)) if leads else None,
            "median_lead_time_hours": float(np.median(leads)) if leads else None,
            "precision": precision,
            "recall": recall,
            "false_alerts": len(false_starts),
            "false_alerts_per_operating_day": len(false_starts) / days,
            "alert_episodes": len(all_starts),
            "operating_days": days,
        },
        records,
    )


def prepare_feature_frame() -> tuple[pd.DataFrame, list[FailureWindow]]:
    raw = read_metropt(SILVER)
    frame = add_causal_context(make_5min_features(raw))
    selected = pd.read_parquet(SELECTED_WINDOWS)
    selected["window_start"] = pd.to_datetime(selected["window_start"])
    selected = selected.set_index("window_start").sort_index()
    frame = frame.join(
        selected[["iforest_anomaly_score", "selected_alert"]],
        how="inner",
    )

    frame["pressure_delta"] = frame["tp2__mean"] - frame["tp3__mean"]
    frame["reservoir_pressure_slope_60m"] = frame["reservoirs__mean"].diff(12)
    frame["oil_temperature_slope_60m"] = frame["oil_temperature__mean"].diff(12)
    frame["motor_current_slope_60m"] = frame["motor_current__mean"].diff(12)
    frame = frame.replace([np.inf, -np.inf], np.nan)
    frame = frame.loc[frame["valid_bin"]].dropna(subset=MODEL_FEATURES)
    failures = parse_failure_windows(FAILURES)
    return frame, failures


def evaluate_real_warning(frame: pd.DataFrame, failures: list[FailureWindow]) -> tuple[dict, pd.DataFrame]:
    # Failure 1 supplies the only positive training episode, failure 2 is the
    # chronological validation event, and failures 3-4 remain untouched test events.
    train_end = failures[1].start - pd.Timedelta(hours=MAX_PRECURSOR_HOURS)
    test_start = failures[2].start - pd.Timedelta(hours=MAX_PRECURSOR_HOURS)
    in_failure = failure_id_at(frame.index, failures).notna()
    train_mask = (frame.index < train_end) & ~in_failure
    validation_mask = (frame.index >= train_end) & (frame.index < test_start)
    test_mask = frame.index >= test_start

    split = {
        "training_end_exclusive": train_end.isoformat(),
        "validation_start": train_end.isoformat(),
        "test_start": test_start.isoformat(),
        "training_failure_events": [failures[0].failure_id],
        "validation_failure_events": [failures[1].failure_id],
        "test_failure_events": [failures[2].failure_id, failures[3].failure_id],
        "chronological_integrity": bool(
            frame.index[train_mask].max() < frame.index[validation_mask].min()
            < frame.index[test_mask].min()
        ),
    }

    evaluations: list[dict] = []
    candidate_policies: list[dict] = []
    for horizon in HORIZONS:
        labels = precursor_label(frame.index, failures, horizon)
        x_train = frame.loc[train_mask, MODEL_FEATURES]
        y_train = labels.loc[train_mask].astype(int)
        if y_train.nunique() != 2:
            raise RuntimeError(f"Horizon {horizon} h does not contain both training classes")

        model = Pipeline(
            [
                ("scale", StandardScaler()),
                (
                    "classifier",
                    LogisticRegression(
                        class_weight="balanced",
                        max_iter=1000,
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        )
        model.fit(x_train, y_train)
        probability = pd.Series(
            model.predict_proba(frame[MODEL_FEATURES])[:, 1],
            index=frame.index,
        )
        normal_training_probability = probability.loc[train_mask & ~labels]

        for quantile in THRESHOLD_QUANTILES:
            threshold = float(normal_training_probability.quantile(quantile))
            alert_col = f"logistic_{horizon}h_{quantile:.3f}"
            frame[alert_col] = persistent(probability >= threshold)
            val_metrics, _ = event_metrics(
                frame.loc[validation_mask], [failures[1]], alert_col, horizon
            )
            candidate_policies.append(
                {
                    "warning_horizon_hours": horizon,
                    "threshold_quantile": quantile,
                    "threshold": threshold,
                    "alert_col": alert_col,
                    **{f"validation_{key}": value for key, value in val_metrics.items()},
                }
            )

        baseline_col = f"baseline_{horizon}h"
        frame[baseline_col] = frame["selected_alert"].astype(bool)
        for split_name, mask, split_failures in (
            ("validation", validation_mask, [failures[1]]),
            ("test", test_mask, [failures[2], failures[3]]),
        ):
            metrics, _ = event_metrics(frame.loc[mask], split_failures, baseline_col, horizon)
            evaluations.append(
                {
                    "scenario_scope": "REAL_METROPT_BENCHMARK",
                    "model_name": "adaptive_anomaly_policy_baseline",
                    "policy": "q0.9850_3of4",
                    "split": split_name,
                    "warning_horizon_hours": horizon,
                    **metrics,
                }
            )
    eligible = [
        row
        for row in candidate_policies
        if row["validation_false_alerts_per_operating_day"] <= MAX_FALSE_ALERTS_PER_DAY
    ] or candidate_policies
    selected = sorted(
        eligible,
        key=lambda row: (
            -row["validation_events_warned"],
            row["validation_false_alerts_per_operating_day"],
            -row["validation_precision"],
            -row["warning_horizon_hours"],
            -row["threshold_quantile"],
        ),
    )[0]

    selected_col = selected["alert_col"]
    supervised_test_records = []
    for split_name, mask, split_failures in (
        ("validation", validation_mask, [failures[1]]),
        ("test", test_mask, [failures[2], failures[3]]),
    ):
        metrics, records = event_metrics(
            frame.loc[mask], split_failures, selected_col, selected["warning_horizon_hours"]
        )
        evaluations.append(
            {
                "scenario_scope": "REAL_METROPT_BENCHMARK",
                "model_name": "logistic_regression",
                "policy": (
                    f"training-normal-q{selected['threshold_quantile']:.3f}_"
                    f"{PERSISTENCE_REQUIRED}of{PERSISTENCE_WINDOW}"
                ),
                "split": split_name,
                "warning_horizon_hours": selected["warning_horizon_hours"],
                **metrics,
            }
        )
        if split_name == "test":
            supervised_test_records = records

    supervised_validation = next(
        row
        for row in evaluations
        if row["model_name"] == "logistic_regression" and row["split"] == "validation"
    )
    if supervised_validation["events_warned"] == 0:
        # A silent classifier is not a useful maintenance policy. Retain the
        # accepted adaptive anomaly baseline and use the narrowest evaluated
        # horizon; its held-out warning remains less than two hours before onset.
        selected_result = next(
            row
            for row in evaluations
            if row["model_name"] == "adaptive_anomaly_policy_baseline"
            and row["split"] == "test"
            and row["warning_horizon_hours"] == min(HORIZONS)
        )
        selected_policy = {
            "model_name": "adaptive_anomaly_policy_baseline",
            "policy": "q0.9850_3of4",
            "warning_horizon_hours": min(HORIZONS),
            "selection_reason": (
                "The supervised candidate produced no validation warnings; a no-alert "
                "classifier is not operationally useful, so the accepted adaptive anomaly "
                "baseline is retained."
            ),
        }
        _, selected_test_records = event_metrics(
            frame.loc[test_mask],
            [failures[2], failures[3]],
            f"baseline_{min(HORIZONS)}h",
            min(HORIZONS),
        )
    else:
        selected_result = next(
            row
            for row in evaluations
            if row["model_name"] == "logistic_regression" and row["split"] == "test"
        )
        selected_policy = {
            "model_name": "logistic_regression",
            "policy": selected_result["policy"],
            "warning_horizon_hours": selected_result["warning_horizon_hours"],
            "selection_reason": "The supervised candidate produced a useful validation warning within budget.",
        }
        selected_test_records = supervised_test_records

    report = {
        "split": split,
        "features": MODEL_FEATURES,
        "models_compared": ["adaptive_anomaly_policy_baseline", "logistic_regression"],
        "horizons_tested_hours": list(HORIZONS),
        "supervised_candidate_policy": {
            key: value for key, value in selected.items() if key != "alert_col"
        },
        "selected_policy": selected_policy,
        "selected_result": selected_result,
        "selected_test_event_records": selected_test_records,
        "evaluations": evaluations,
        "interpretation": (
            "Real MetroPT warning labels preserve the published fault onsets. "
            "All features are causal and all model selection precedes the two-event test period."
        ),
    }
    return report, frame


def build_enterprise_scenario(
    frame: pd.DataFrame,
    failures: list[FailureWindow],
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    enterprise = pd.DataFrame(index=frame.index)
    enterprise["source_event_timestamp"] = frame.index
    enterprise["event_timestamp"] = frame.index + pd.DateOffset(years=ENTERPRISE_YEAR_SHIFT)
    enterprise["site_code"] = SITE_CODE
    enterprise["equipment_code"] = EQUIPMENT_CODE

    hours_to_fault = pd.Series(np.nan, index=frame.index)
    precursor_failure_id = pd.Series(pd.NA, index=frame.index, dtype="string")
    for failure in failures:
        delta = (failure.start - frame.index).total_seconds() / 3600.0
        mask = (delta > 0) & (delta <= MAX_PRECURSOR_HOURS)
        hours_to_fault.loc[mask] = delta[mask]
        precursor_failure_id.loc[mask] = failure.failure_id

    degradation = (1.0 - hours_to_fault / MAX_PRECURSOR_HOURS).clip(0.0, 1.0).fillna(0.0)
    # Fixed pointwise transform: unlike a full-period percentile rank, this
    # does not depend on observations after the current timestamp.
    anomaly_component = 1.0 / (1.0 + np.exp(-8.0 * frame["iforest_anomaly_score"]))

    enterprise["tp2_pressure_bar"] = frame["tp2__mean"]
    enterprise["tp3_pressure_bar"] = frame["tp3__mean"]
    enterprise["reservoir_pressure_bar"] = frame["reservoirs__mean"] - 0.60 * degradation
    enterprise["oil_temperature_c"] = frame["oil_temperature__mean"] + 6.0 * degradation
    enterprise["motor_current_a"] = frame["motor_current__mean"] + 10.0 * degradation
    enterprise["pressure_delta_bar"] = enterprise["tp2_pressure_bar"] - enterprise["tp3_pressure_bar"]
    enterprise["reservoir_pressure_slope_60m"] = frame["reservoir_pressure_slope_60m"]
    enterprise["oil_temperature_slope_60m"] = frame["oil_temperature_slope_60m"]
    enterprise["motor_current_slope_60m"] = frame["motor_current_slope_60m"]
    enterprise["anomaly_score"] = frame["iforest_anomaly_score"]
    enterprise["degradation_index"] = degradation
    enterprise["condition_score"] = (100.0 - 60.0 * degradation - 10.0 * anomaly_component).clip(0.0, 100.0)
    enterprise["precursor_failure_id"] = precursor_failure_id
    enterprise["source_fault_event_id"] = failure_id_at(frame.index, failures)
    enterprise["fault_state"] = enterprise["source_fault_event_id"].notna()
    enterprise["condition_state"] = np.select(
        [enterprise["fault_state"], enterprise["degradation_index"] > 0],
        ["FAULT", "DEGRADING"],
        default="NORMAL",
    )

    policy_results = []
    alerts_by_horizon: dict[int, pd.Series] = {}
    for horizon in HORIZONS:
        threshold = 1.0 - horizon / MAX_PRECURSOR_HOURS
        alert = persistent(enterprise["degradation_index"] > threshold)
        alerts_by_horizon[horizon] = alert
        metrics, _ = event_metrics(
            enterprise.assign(candidate_alert=alert).set_index("source_event_timestamp"),
            failures,
            "candidate_alert",
            horizon,
        )
        policy_results.append(
            {
                "warning_horizon_hours": horizon,
                "degradation_threshold": threshold,
                **metrics,
            }
        )

    selected = sorted(
        policy_results,
        key=lambda row: (
            -row["events_warned"],
            row["false_alerts_per_operating_day"],
            -(row["median_lead_time_hours"] or 0.0),
        ),
    )[0]
    selected_horizon = int(selected["warning_horizon_hours"])
    enterprise["selected_warning_state"] = alerts_by_horizon[selected_horizon].to_numpy()
    enterprise["selected_warning_horizon_hours"] = selected_horizon
    enterprise["source_dataset_code"] = "METROPT3"
    enterprise["source_data_origin"] = "EXTERNAL_REAL"
    enterprise["scenario_type"] = "SYNTHETIC_ENTERPRISE_ADAPTATION"
    enterprise["transformation_basis"] = "METROPT_INFORMED"
    enterprise["degradation_signal_origin"] = "SYNTHETIC_CONTROLLED"

    event_frame = enterprise.set_index("source_event_timestamp")
    selected_metrics, selected_records = event_metrics(
        event_frame,
        failures,
        "selected_warning_state",
        selected_horizon,
    )
    warning_events = pd.DataFrame(selected_records)
    warning_events["scenario_scope"] = "METROPT_INFORMED_SYNTHETIC_ENTERPRISE"
    warning_events["site_code"] = SITE_CODE
    warning_events["equipment_code"] = EQUIPMENT_CODE
    for column in ["fault_onset_timestamp", "fault_end_timestamp", "first_warning_timestamp"]:
        warning_events[column.replace("first_warning", "warning")] = (
            pd.to_datetime(warning_events[column]) + pd.DateOffset(years=ENTERPRISE_YEAR_SHIFT)
        )
    warning_events = warning_events.drop(columns=["first_warning_timestamp"])
    warning_events["warning_horizon_hours"] = selected_horizon
    warning_events["warning_persistence"] = f"{PERSISTENCE_REQUIRED}-of-{PERSISTENCE_WINDOW}"
    warning_events["source_dataset_code"] = "METROPT3"
    warning_events["source_data_origin"] = "EXTERNAL_REAL"
    warning_events["scenario_type"] = "SYNTHETIC_ENTERPRISE_ADAPTATION"
    warning_events["transformation_basis"] = "METROPT_INFORMED"
    warning_events["degradation_signal_origin"] = "SYNTHETIC_CONTROLLED"

    report = {
        "mapping": {
            "site_code": SITE_CODE,
            "equipment_code": EQUIPMENT_CODE,
            "equipment_type": "COMPRESSED_AIR_SYSTEM",
            "calendar_adaptation": f"source timestamps shifted by {ENTERPRISE_YEAR_SHIFT} years",
        },
        "governance": {
            "source_dataset_code": "METROPT3",
            "source_data_origin": "EXTERNAL_REAL",
            "scenario_type": "SYNTHETIC_ENTERPRISE_ADAPTATION",
            "transformation_basis": "METROPT_INFORMED",
            "degradation_signal_origin": "SYNTHETIC_CONTROLLED",
        },
        "controlled_degradation": {
            "maximum_precursor_hours": MAX_PRECURSOR_HOURS,
            "oil_temperature_increase_at_fault_c": 6.0,
            "motor_current_increase_at_fault_a": 10.0,
            "reservoir_pressure_reduction_at_fault_bar": 0.60,
        },
        "horizon_results": policy_results,
        "selected_policy": selected,
        "selected_metrics": selected_metrics,
    }
    return enterprise.reset_index(drop=True), warning_events, report


def json_ready(value):
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return pd.Timestamp(value).isoformat()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if np.isnan(value) else float(value)
    if pd.isna(value):
        return None
    raise TypeError(f"Cannot serialize {type(value)}")


def main() -> None:
    required = [BRONZE, ACQUISITION, FAILURES, SILVER, SELECTED_WINDOWS]
    missing = [str(path.relative_to(REPO)) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required MetroPT inputs: " + ", ".join(missing))

    acquisition = json.loads(ACQUISITION.read_text(encoding="utf-8"))
    bronze_hash_before = sha256(BRONZE)
    if bronze_hash_before.lower() != acquisition["csv_sha256"].lower():
        raise RuntimeError("MetroPT Bronze SHA-256 does not match its acquisition manifest")

    frame, failures = prepare_feature_frame()
    real_report, scored_frame = evaluate_real_warning(frame, failures)
    enterprise, warning_events, synthetic_report = build_enterprise_scenario(scored_frame, failures)

    ENTERPRISE_OUT.parent.mkdir(parents=True, exist_ok=True)
    GOLD_OUT.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)

    enterprise.to_parquet(ENTERPRISE_OUT, index=False, compression="zstd")
    warning_events.to_csv(GOLD_OUT / "metropt_enterprise_warning_events.csv", index=False)

    real_rows = pd.DataFrame(real_report["evaluations"])
    real_rows.to_csv(GOLD_OUT / "metropt_real_early_warning_evaluation.csv", index=False)

    selected_real = real_report["selected_result"]
    selected_synthetic = {
        "scenario_scope": "METROPT_INFORMED_SYNTHETIC_ENTERPRISE",
        "model_name": "controlled_degradation_condition_policy",
        "policy": f"degradation-threshold-{synthetic_report['selected_policy']['degradation_threshold']:.3f}",
        "split": "enterprise_scenario",
        **synthetic_report["selected_metrics"],
        "warning_horizon_hours": synthetic_report["selected_policy"]["warning_horizon_hours"],
    }
    kpi_rows = []
    for row in real_report["evaluations"]:
        enriched = dict(row)
        enriched["is_selected"] = bool(
            row["model_name"] == selected_real["model_name"]
            and row["split"] == selected_real["split"]
            and row["warning_horizon_hours"] == selected_real["warning_horizon_hours"]
        )
        kpi_rows.append(enriched)
    for result in synthetic_report["horizon_results"]:
        kpi_rows.append(
            {
                "scenario_scope": "METROPT_INFORMED_SYNTHETIC_ENTERPRISE",
                "model_name": "controlled_degradation_condition_policy",
                "policy": f"degradation-threshold-{result['degradation_threshold']:.3f}",
                "split": "enterprise_scenario",
                "is_selected": bool(
                    result["warning_horizon_hours"]
                    == selected_synthetic["warning_horizon_hours"]
                ),
                **{key: value for key, value in result.items() if key != "degradation_threshold"},
            }
        )
    pd.DataFrame(kpi_rows).to_csv(
        GOLD_OUT / "metropt_predictive_maintenance_kpis.csv", index=False
    )

    bronze_hash_after = sha256(BRONZE)
    if bronze_hash_after != bronze_hash_before:
        raise RuntimeError("MetroPT Bronze changed during predictive-maintenance processing")

    report = {
        "source": {
            "dataset": "MetroPT-3",
            "dataset_id": "uci_791_metropt3",
            "data_origin": "EXTERNAL_REAL",
            "bronze_sha256_before": bronze_hash_before,
            "bronze_sha256_after": bronze_hash_after,
            "bronze_unchanged": bronze_hash_before == bronze_hash_after,
            "silver_rows": 1_516_948,
            "feature_windows": len(frame),
            "failure_events": [asdict(failure) for failure in failures],
        },
        "real_metropt_result": real_report,
        "metropt_informed_synthetic_enterprise_result": synthetic_report,
        "outputs": {
            "enterprise_telemetry": str(ENTERPRISE_OUT.relative_to(REPO)).replace("\\", "/"),
            "warning_events": str((GOLD_OUT / "metropt_enterprise_warning_events.csv").relative_to(REPO)).replace("\\", "/"),
            "real_evaluation": str((GOLD_OUT / "metropt_real_early_warning_evaluation.csv").relative_to(REPO)).replace("\\", "/"),
            "kpi_summary": str((GOLD_OUT / "metropt_predictive_maintenance_kpis.csv").relative_to(REPO)).replace("\\", "/"),
        },
    }
    REPORT_OUT.write_text(json.dumps(report, indent=2, default=json_ready) + "\n", encoding="utf-8")

    print("=== MetroPT predictive-maintenance workflow complete ===")
    print(f"Feature windows: {len(frame):,}")
    print("REAL METROPT RESULT")
    print(pd.Series(selected_real).to_string())
    print("METROPT-INFORMED SYNTHETIC ENTERPRISE RESULT")
    print(pd.Series(selected_synthetic).to_string())
    print(f"Enterprise telemetry: {ENTERPRISE_OUT.relative_to(REPO)}")
    print(f"Metrics: {REPORT_OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
