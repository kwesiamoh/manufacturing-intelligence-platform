from __future__ import annotations

from pathlib import Path
import json

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

TARGETS = [
    "cooler_condition_pct",
    "valve_condition_pct",
    "internal_pump_leakage_class",
    "hydraulic_accumulator_bar",
    "stable_flag",
]


def repo_root() -> Path:
    here = Path.cwd()
    for c in [here, *here.parents]:
        if (c / "sources" / "step04-reliability").exists():
            return c
    raise FileNotFoundError("Could not locate sources/step04-reliability.")


def classwise_temporal_split(d: pd.DataFrame, target: str):
    train_parts = []
    test_parts = []

    for cls, g in d.groupby(target, sort=True):
        g = g.sort_values("cycle_id").reset_index(drop=True)

        if len(g) < 5:
            raise ValueError(
                f"Target {target}, class {cls} has only {len(g)} rows; "
                "too few for an 80/20 class-wise temporal split."
            )

        cut = int(np.floor(len(g) * (1 - HOLDOUT_FRACTION)))
        cut = max(1, min(cut, len(g) - 1))

        train_parts.append(g.iloc[:cut].copy())
        test_parts.append(g.iloc[cut:].copy())

    train = (
        pd.concat(train_parts, ignore_index=True)
        .sort_values("cycle_id")
        .reset_index(drop=True)
    )
    test = (
        pd.concat(test_parts, ignore_index=True)
        .sort_values("cycle_id")
        .reset_index(drop=True)
    )

    return train, test


def majority_baseline(y_train: pd.Series, y_test: pd.Series) -> dict:
    majority = y_train.value_counts().idxmax()
    pred = np.repeat(majority, len(y_test))

    return {
        "majority_class": int(majority),
        "accuracy": float(accuracy_score(y_test, pred)),
        "balanced_accuracy": float(
            balanced_accuracy_score(y_test, pred)
        ),
        "macro_f1": float(
            f1_score(y_test, pred, average="macro", zero_division=0)
        ),
    }


def evaluate_target(
    data: pd.DataFrame,
    feature_cols: list[str],
    target: str,
    out_dir: Path,
    model_dir: Path,
) -> dict:
    work = data.sort_values("cycle_id").reset_index(drop=True).copy()

    train, test = classwise_temporal_split(work, target)

    train_counts = train[target].value_counts().sort_index()
    test_counts = test[target].value_counts().sort_index()

    print(f"\n=== {target} ===")
    print(f"Rows: train={len(train)}, holdout={len(test)}")
    print("Train class counts:")
    print(train_counts.to_string())
    print("Holdout class counts:")
    print(test_counts.to_string())

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

    labels = sorted(work[target].unique().tolist())

    scores = {
        "accuracy": float(accuracy_score(test[target], pred)),
        "balanced_accuracy": float(
            balanced_accuracy_score(test[target], pred)
        ),
        "macro_f1": float(
            f1_score(test[target], pred, average="macro", zero_division=0)
        ),
    }

    report = classification_report(
        test[target],
        pred,
        labels=labels,
        output_dict=True,
        zero_division=0,
    )

    cm = confusion_matrix(test[target], pred, labels=labels)
    pd.DataFrame(
        cm,
        index=[f"actual_{x}" for x in labels],
        columns=[f"pred_{x}" for x in labels],
    ).to_csv(out_dir / f"{target}_confusion_matrix_corrected.csv")

    pred_out = test[["cycle_id", target]].copy()
    pred_out["predicted"] = pred
    pred_out["correct"] = pred_out[target] == pred_out["predicted"]
    pred_out.to_csv(
        out_dir / f"{target}_holdout_predictions_corrected.csv",
        index=False,
    )

    fi = pd.DataFrame({
        "feature": feature_cols,
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False)
    fi.to_csv(
        out_dir / f"{target}_feature_importance_corrected.csv",
        index=False,
    )

    joblib.dump(
        model,
        model_dir / f"{target}_extra_trees_corrected.joblib",
    )

    print(f"Baseline macro F1:     {baseline['macro_f1']:.4f}")
    print(f"Model macro F1:        {scores['macro_f1']:.4f}")
    print(f"Model balanced acc:    {scores['balanced_accuracy']:.4f}")
    print(f"Model accuracy:        {scores['accuracy']:.4f}")

    return {
        "target": target,
        "train_rows": int(len(train)),
        "holdout_rows": int(len(test)),
        "train_class_counts": {
            str(k): int(v) for k, v in train_counts.items()
        },
        "holdout_class_counts": {
            str(k): int(v) for k, v in test_counts.items()
        },
        "majority_baseline": baseline,
        "extra_trees": scores,
        "classification_report": report,
        "top_features": fi.head(15).to_dict(orient="records"),
    }


def main():
    repo = repo_root()

    silver = repo / "sources" / "step04-reliability" / "silver" / "reliability"
    labels_path = silver / "condition_labels.parquet"

    out_dir = repo / "data" / "gold" / "advanced_analytics" / "hydraulic_condition"
    report_dir = repo / "reports" / "advanced_analytics"
    model_dir = repo / "models" / "advanced_analytics" / "hydraulic_condition"

    for p in [out_dir, report_dir, model_dir]:
        p.mkdir(parents=True, exist_ok=True)

    feature_path = out_dir / "hydraulic_cycle_features.parquet"
    if not feature_path.exists():
        raise FileNotFoundError(
            "hydraulic_cycle_features.parquet not found. "
            "Run Stage 13E.2 once first to create cycle features."
        )

    print("=== Stage 13E.3 corrected hydraulic condition classification ===")

    features = pd.read_parquet(feature_path)
    labels = pq.ParquetFile(labels_path).read().to_pandas()
    labels["cycle_id"] = labels["cycle_id"].astype(int)

    data = labels.merge(
        features,
        on="cycle_id",
        how="inner",
        validate="one_to_one",
    )

    if len(data) != 2205:
        raise ValueError(f"Expected 2205 aligned cycles, got {len(data)}.")

    feature_cols = [c for c in features.columns if c != "cycle_id"]

    print(f"Cycles: {len(data)}")
    print(f"Features: {len(feature_cols)}")

    results = {}
    summary_rows = []

    for target in TARGETS:
        r = evaluate_target(
            data=data,
            feature_cols=feature_cols,
            target=target,
            out_dir=out_dir,
            model_dir=model_dir,
        )
        results[target] = r

        summary_rows.append({
            "target": target,
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
    summary.to_csv(
        out_dir / "condition_model_summary_corrected.csv",
        index=False,
    )

    report = {
        "source": {
            "source_code": "HYDRAULIC_CM",
            "is_real_data": True,
            "note": (
                "Real external hydraulic condition-monitoring benchmark; "
                "not beverage-plant operational data."
            ),
        },
        "design": {
            "cycle_count": int(len(data)),
            "feature_count": int(len(feature_cols)),
            "model": "ExtraTreesClassifier",
            "split": (
                "class-wise chronological 80/20 split: within each target "
                "class, earliest 80% of cycles train and latest 20% test"
            ),
            "reason_for_split": (
                "A single global chronological split produced holdouts missing "
                "entire classes because experimental condition classes occur "
                "in long contiguous blocks."
            ),
            "stable_cycle_filter": False,
            "stable_flag_treatment": (
                "stable_flag is evaluated as its own classification target and "
                "is not used to remove cycles from the physical-condition tasks."
            ),
            "primary_metrics": ["macro_f1", "balanced_accuracy"],
            "baseline": "majority class",
        },
        "targets": results,
        "limitations": [
            "This is condition classification, not failure forecasting or RUL prediction.",
            "Class-wise temporal splitting tests later cycles within each known class but is not a forward calendar forecast.",
            "The hydraulic benchmark remains separate from the synthetic beverage-enterprise reliability layer.",
            "Cycle-level summary statistics compress the original sensor waveforms."
        ],
    }

    report_path = (
        report_dir
        / "stage13e3_corrected_hydraulic_condition_classification.json"
    )
    report_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("\n=== Corrected model summary ===")
    print(summary.to_string(index=False))

    print("\nReport:")
    print(report_path.relative_to(repo))
    print("=== Stage 13E.3 complete ===")


if __name__ == "__main__":
    main()
