from __future__ import annotations

import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "bronze" / "secom"
OUT = ROOT / "silver" / "quality"
OUT.mkdir(parents=True, exist_ok=True)

features = pd.read_csv(RAW / "secom.data", sep=r"\s+", header=None, na_values=["NaN"])
labels = pd.read_csv(
    RAW / "secom_labels.data",
    sep=r"\s+",
    header=None,
    names=["raw_label", "timestamp_text"],
    quotechar='"',
)

if len(features) != len(labels):
    raise ValueError("Feature/label row-count mismatch")

features.columns = [f"sensor_{i:03d}" for i in range(1, features.shape[1] + 1)]
labels["event_timestamp"] = pd.to_datetime(
    labels["timestamp_text"], format="%d/%m/%Y %H:%M:%S", errors="raise"
)
labels["quality_result"] = labels["raw_label"].map({-1: "PASS", 1: "FAIL"})
labels.insert(0, "sample_id", [f"SECOM-{i:06d}" for i in range(1, len(labels) + 1)])

silver = pd.concat(
    [labels[["sample_id", "event_timestamp", "raw_label", "quality_result"]], features],
    axis=1,
)

# Preserve missing sensor values. No imputation is performed in the Silver layer.
silver.to_parquet(OUT / "secom_process_quality.parquet", index=False, compression="snappy")

# Compact analytical label table for SQL/BI integration.
labels[["sample_id", "event_timestamp", "raw_label", "quality_result"]].to_parquet(
    OUT / "secom_quality_events.parquet", index=False, compression="snappy"
)

print("Created Silver Parquet files in", OUT)
