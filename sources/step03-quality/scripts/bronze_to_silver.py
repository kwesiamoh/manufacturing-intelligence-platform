from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]

FEATURES = BASE / "bronze" / "secom" / "secom.data"
LABELS = BASE / "bronze" / "secom" / "secom_labels.data"
OUT = BASE / "silver" / "quality"

OUT.mkdir(parents=True, exist_ok=True)

if not FEATURES.exists():
    raise FileNotFoundError(f"Missing: {FEATURES}")

if not LABELS.exists():
    raise FileNotFoundError(f"Missing: {LABELS}")

features = pd.read_csv(
    FEATURES,
    sep=r"\s+",
    header=None,
    na_values=["NaN"]
)

features.columns = [f"sensor_{i:03d}" for i in range(features.shape[1])]

labels = pd.read_csv(
    LABELS,
    sep=r"\s+",
    header=None,
    names=["quality_label", "timestamp"]
)

if len(features) != len(labels):
    raise RuntimeError(
        f"Row mismatch: features={len(features)}, labels={len(labels)}"
    )

quality = pd.concat(
    [
        labels.reset_index(drop=True),
        features.reset_index(drop=True)
    ],
    axis=1
)

quality["quality_result"] = quality["quality_label"].map({
    -1: "PASS",
    1: "FAIL"
})

quality.insert(
    0,
    "record_id",
    range(1, len(quality) + 1)
)

out_file = OUT / "secom_quality.parquet"

quality.to_parquet(
    out_file,
    index=False,
    engine="pyarrow",
    compression="zstd"
)

print(f"Rows: {len(quality):,}")
print(f"Sensor columns: {features.shape[1]}")
print(f"Missing sensor values: {features.isna().sum().sum():,}")
print(f"PASS: {(quality['quality_label'] == -1).sum():,}")
print(f"FAIL: {(quality['quality_label'] == 1).sum():,}")
print(f"Silver dataset written to: {out_file}")
print("No synthetic sensor measurements or quality labels were created.")
