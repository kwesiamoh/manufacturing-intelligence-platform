from __future__ import annotations

import json
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "bronze" / "secom"
META = ROOT / "metadata"

features_path = RAW / "secom.data"
labels_path = RAW / "secom_labels.data"

if not features_path.exists() or not labels_path.exists():
    raise SystemExit("Raw SECOM files are missing. Run download_source.py first.")

features = pd.read_csv(features_path, sep=r"\s+", header=None, na_values=["NaN"])
labels = pd.read_csv(
    labels_path,
    sep=r"\s+",
    header=None,
    names=["raw_label", "timestamp_text"],
    quotechar='"',
)

profile = {
    "feature_rows": int(features.shape[0]),
    "sensor_columns_observed": int(features.shape[1]),
    "label_rows": int(labels.shape[0]),
    "missing_sensor_values": int(features.isna().sum().sum()),
    "pass_count": int((labels["raw_label"] == -1).sum()),
    "fail_count": int((labels["raw_label"] == 1).sum()),
    "unexpected_labels": sorted(set(labels["raw_label"].dropna()) - {-1, 1}),
}

profile["row_counts_match"] = profile["feature_rows"] == profile["label_rows"]
profile["expected_1567_rows"] = profile["feature_rows"] == 1567

(META / "observed_bronze_profile.json").write_text(
    json.dumps(profile, indent=2), encoding="utf-8"
)

if not profile["row_counts_match"]:
    raise SystemExit("Validation failed: feature and label row counts differ.")
if not profile["expected_1567_rows"]:
    raise SystemExit("Validation failed: expected 1,567 UCI SECOM records.")
if profile["unexpected_labels"]:
    raise SystemExit(f"Validation failed: unexpected labels {profile['unexpected_labels']}")

print(json.dumps(profile, indent=2))
