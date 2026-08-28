from __future__ import annotations

from pathlib import Path
import json
import math

import joblib
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)


RANDOM_STATE = 42
HOLDOUT_FRACTION = 0.20

CONDITION_TARGETS = [
    "cooler_condition_pct",
    "valve_condition_pct",
    "internal_pump_leakage_class",
    "hydraulic_accumulator_bar",
]

ALL_TARGETS = CONDITION_TARGETS + ["stable_flag"]


def repo_root() -> Path:
    here = Path.cwd()
    for c in [here, *here.parents]:
        if (c / "sources" / "step04-reliability").exists():
            return c
    raise FileNotFoundError("Could not locate sources/step04-reliability.")


def merge_partial_stats(parts: list[pd.DataFrame]) -> pd.DataFrame:
    d = pd.concat(parts, ignore_index=True)

    g = d.groupby("cycle_id", as_index=False).agg(
        n=("n", "sum"),
        sum_x=("sum_x", "sum"),
        sum_x2=("sum_x2", "sum"),
        min_x=("min_x", "min"),
        max_x=("max_x", "max"),
    )

    g["mean"] = g["sum_x"] / g["n"]
    var = (g["sum_x2"] / g["n"]) - (g["mean"] ** 2)
    g["std"] = np.sqrt(var.clip(lower=0))
    g["rms"] = np.sqrt((g["sum_x2"] / g["n"]).clip(lower=0))
    g["range"] = g["max_x"] - g["min_x"]

    return g[["cycle_id", "mean", "std", "min_x", "max_x", "range", "rms"]]


def build_cycle_features(telemetry_root: Path) -> pd.DataFrame:
    sensor_dirs = sorted([p for p in telemetry_root.glob("sensor_id=*") if p.is_dir()])

    sensor_frames = []

    print("=== Cycle feature extraction ===")

    for sd in sensor_dirs:
        sensor = sd.name.split("=", 1)[1]
        files = sorted(sd.glob("*.parquet"))
        partials = []

        print(f"Processing {sensor}: {len(files)} files")

        for p in files:
            pf = pq.ParquetFile(p)
            table = pf.read(columns=["cycle_id", "value"])
            x = table.to_pandas()
            x["value"] = pd.to_numeric(x["value"], errors="coerce")
            x = x.dropna(subset=["cycle_id", "value"])

            x["value_sq"] = x["value"] * x["value"]

            part = (
                x.groupby("cycle_id", as_index=False)
                .agg(
                    n=("value", "count"),
                    sum_x=("value", "sum"),
                    sum_x2=("value_sq", "sum"),
                    min_x=("value", "min"),
                    max_x=("value", "max"),
                )
            )
            partials.append(part)

        s = merge_partial_stats(partials)
        rename = {
            "mean": f"{sensor}__mean",
            "std": f"{sensor}__std",
            "min_x": f"{sensor}__min",
            "max_x": f"{sensor}__max",
            "range": f"{sensor}__range",
            "rms": f"{sensor}__rms",
        }
        s = s.rename(columns=rename)
        sensor_frames.append(s)

    features = sensor_frames[0]
    for s in sensor_frames[1:]:
        features = features.merge(s, on="cycle_id", how="inner", validate="one_to_one")

    features = features.sort_values("cycle_id").reset_index(drop=True)
    return features


def majority_baseline(y_train: pd.Series, y_test: pd.Series) -> dict:
    majority = y_train.value_counts().idxmax()
    pred = np.repeat(majority, len(y_test))

    return {
        "majority_class": int(majority),
        "accuracy": float(accuracy_score(y_test, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, pred)),
        "macro_f1": float(f1_score(y_test, pred, average="macro", zero_division=0)),
    }


def evaluate_target(
    d: pd.DataFrame,
    feature_cols: list[str],
    target: str,
    stable_only: bool,
    out_dir: Path,
    model_dir: Path,
) -> dict:

    work = d.copy()
    if stable_only:
        work = work.loc[work["stable_flag"] == 1].copy()

    work = work.sort_values("cycle_id").reset_index(drop=True)

    split = int(len(work) * (1 - HOLDOUT_FRACTION))
    train = work.iloc[:split].copy()
    test = work.iloc[split:].copy()

    train_classes = sorted(train[target].unique().tolist())
    test_classes = sorted(test[target].unique().tolist())

    print(f"\n=== {target} ===")
    print(f"Stable-only: {stable_only}")
    print(f"Rows: train={len(train)}, holdout={len(test)}")
    print(f"Cycle range train: {train.cycle_id.min()} -> {train.cycle_id.max()}")
    print(f"Cycle range test:  {test.cycle_id.min()} -> {test.cycle_id.max()}")
    print(f"Train classes: {train_classes}")
    print(f"Test classes:  {test_classes}")

    baseline = majority_baseline(train[target], test[target])

    model = ExtraTreesClassifier(
        n_estimators=500,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    model.fit(train[feature_cols], train[target])
    pred = model.predict(test[feature_cols])

    labels = sorted(set(train[target].tolist()) | set(test[target].tolist()))

    model_metrics = {
        "accuracy": float(accuracy_score(test[target], pred)),
        "balanced_accuracy": float(balanced_accuracy_score(test[target], pred)),
        "macro_f1": float(f1_score(test[target], pred, average="macro", zero_division=0)),
    }

    report = classification_report(
        test[target],
        pred,
        labels=labels,
        output_dict=True,
        zero_division=0,
    )

    cm = confusion_matrix(test[target], pred, labels=labels)
    cm_df = pd.DataFrame(
        cm,
        index=[f"actual_{x}" for x in labels],
        columns=[f"pred_{x}" for x in labels],
    )
    cm_df.to_csv(out_dir / f"{target}_confusion_matrix.csv")

    pred_out = test[["cycle_id", target]].copy()
    pred_out["predicted"] = pred
    pred_out["correct"] = pred_out[target] == pred_out["predicted"]
    pred_out.to_csv(out_dir / f"{target}_holdout_predictions.csv", index=False)

    fi = pd.DataFrame({
        "feature": feature_cols,
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False)
    fi.to_csv(out_dir / f"{target}_feature_importance.csv", index=False)

    joblib.dump(model, model_dir / f"{target}_extra_trees.joblib")

    print(f"Baseline macro F1: {baseline['macro_f1']:.4f}")
    print(f"Model macro F1:    {model_metrics['macro_f1']:.4f}")
    print(f"Model balanced acc:{model_metrics['balanced_accuracy']:.4f}")
    print(f"Model accuracy:    {model_metrics['accuracy']:.4f}")

    return {
        "target": target,
        "stable_only": stable_only,
        "rows_total_for_task": int(len(work)),
        "train_rows": int(len(train)),
        "holdout_rows": int(len(test)),
        "train_cycle_min": int(train["cycle_id"].min()),
        "train_cycle_max": int(train["cycle_id"].max()),
        "holdout_cycle_min": int(test["cycle_id"].min()),
        "holdout_cycle_max": int(test["cycle_id"].max()),
        "train_class_counts": {
            str(k): int(v) for k, v in train[target].value_counts().sort_index().items()
        },
        "holdout_class_counts": {
            str(k): int(v) for k, v in test[target].value_counts().sort_index().items()
        },
        "majority_baseline": baseline,
        "extra_trees": model_metrics,
        "classification_report": report,
        "top_features": fi.head(15).to_dict(orient="records"),
    }


def main():
    repo = repo_root()

    base = repo / "sources" / "step04-reliability" / "silver" / "reliability"
    telemetry = base / "telemetry"
    labels_path = base / "condition_labels.parquet"

    out_dir = repo / "data" / "gold" / "advanced_analytics" / "hydraulic_condition"
    report_dir = repo / "reports" / "advanced_analytics"
    model_dir = repo / "models" / "advanced_analytics" / "hydraulic_condition"

    for p in [out_dir, report_dir, model_dir]:
        p.mkdir(parents=True, exist_ok=True)

    print("=== Stage 13E.2 real hydraulic condition classification ===")

    feature_path = out_dir / "hydraulic_cycle_features.parquet"

    if feature_path.exists():
        print(f"Using existing cycle features: {feature_path.relative_to(repo)}")
        features = pd.read_parquet(feature_path)
    else:
        features = build_cycle_features(telemetry)
        features.to_parquet(feature_path, index=False)
        print(f"\nCycle features written: {feature_path.relative_to(repo)}")

    labels = pq.ParquetFile(labels_path).read().to_pandas()
    labels["cycle_id"] = labels["cycle_id"].astype(int)

    data = labels.merge(features, on="cycle_id", how="inner", validate="one_to_one")

    print(f"Cycles after feature-label join: {len(data)}")
    print(f"Feature columns: {len(features.columns) - 1}")

    if len(data) != len(labels):
        raise ValueError(
            f"Expected {len(labels)} labeled cycles but joined {len(data)}."
        )

    feature_cols = [c for c in features.columns if c != "cycle_id"]

    results = {}

    # Four physical-condition targets are evaluated only where the source says
    # steady/static conditions were reached.
    for target in CONDITION_TARGETS:
        results[target] = evaluate_target(
            data,
            feature_cols,
            target,
            stable_only=True,
            out_dir=out_dir,
            model_dir=model_dir,
        )

    # Stability itself is a separate classification task on all cycles.
    results["stable_flag"] = evaluate_target(
        data,
        feature_cols,
        "stable_flag",
        stable_only=False,
        out_dir=out_dir,
        model_dir=model_dir,
    )

    summary_rows = []
    for target, r in results.items():
        summary_rows.append({
            "target": target,
            "stable_only": r["stable_only"],
            "train_rows": r["train_rows"],
            "holdout_rows": r["holdout_rows"],
            "baseline_macro_f1": r["majority_baseline"]["macro_f1"],
            "model_macro_f1": r["extra_trees"]["macro_f1"],
            "model_balanced_accuracy": r["extra_trees"]["balanced_accuracy"],
            "model_accuracy": r["extra_trees"]["accuracy"],
            "macro_f1_improvement_vs_baseline": (
                r["extra_trees"]["macro_f1"]
                - r["majority_baseline"]["macro_f1"]
            ),
        })

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(out_dir / "condition_model_summary.csv", index=False)

    report = {
        "source": {
            "source_code": "HYDRAULIC_CM",
            "is_real_data": True,
            "role": "OPERATIONAL",
            "note": (
                "Real external hydraulic condition-monitoring benchmark. "
                "It is not beverage-plant operational data and is not joined "
                "to the synthetic enterprise maintenance facts."
            ),
        },
        "design": {
            "cycle_count": int(len(data)),
            "sensor_count": int(len(feature_cols) / 6),
            "feature_count": int(len(feature_cols)),
            "features_per_sensor": ["mean", "std", "min", "max", "range", "rms"],
            "model": "ExtraTreesClassifier",
            "holdout": "final 20% of cycles, time ordered",
            "primary_metrics": ["macro_f1", "balanced_accuracy"],
            "baseline": "majority class",
            "condition_targets_use_stable_cycles_only": True,
            "stable_flag_uses_all_cycles": True,
        },
        "targets": results,
        "limitations": [
            "This is condition classification, not remaining-useful-life prediction.",
            "The external hydraulic benchmark is separate from the synthetic beverage enterprise.",
            "Cycle-level summary statistics intentionally compress the raw sensor traces.",
            "Time-ordered holdout is deliberately stricter than a random train/test split.",
        ],
    }

    report_path = report_dir / "stage13e2_hydraulic_condition_classification.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n=== Model summary ===")
    print(summary.to_string(index=False))

    print("\nOutputs:")
    print(out_dir.relative_to(repo))
    print(report_path.relative_to(repo))
    print(model_dir.relative_to(repo))
    print("=== Stage 13E.2 complete ===")


if __name__ == "__main__":
    main()
