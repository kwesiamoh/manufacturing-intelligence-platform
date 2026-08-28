# Step 2 — Real equipment telemetry: MetroPT-3

This increment adds a real industrial equipment-telemetry source for the manufacturing intelligence platform. It does not create synthetic telemetry.

## Source

- Dataset: MetroPT-3 (UCI ID 791)
- DOI: 10.24432/C5VW3R
- License: CC BY 4.0
- Context: compressor Air Production Unit on an operational metro train
- Expected records: 1,516,948
- Documented sensor features: 15

## Why the 208 MB raw CSV is not inside this package

The official UCI archive is larger than the binary transfer limit available to the current execution environment. The source has therefore **not** been replaced by generated data or by a partial imitation. `ingestion/batch/download_metropt3.py` acquires the exact official archive when run in an internet-enabled local environment, verifies the archive against a recorded reproducibility hash, extracts the raw CSV unchanged, and writes an acquisition manifest containing checksums.

## Workflow

1. Install dependencies:

   `python -m pip install -r requirements-step2.txt`

2. Acquire Bronze source:

   `python ingestion/batch/download_metropt3.py`

3. Validate the untouched raw source:

   `python pipelines/validate_metropt3.py`

4. Convert incrementally to Silver Parquet:

   `python pipelines/transform_metropt3.py`

The transformation reads the CSV in chunks so the entire source does not need to be loaded into RAM at once.

## Provenance rule

The four rows in `data/bronze/metropt3/reference/failure_windows.csv` reproduce the failure-window metadata shown on the UCI MetroPT-3 dataset page. They are reference metadata, not generated failures. The sensor dictionary is likewise based on UCI's published variable descriptions.

No integration with the Step 1 steel-energy dataset is performed yet. Cross-domain integration comes later after each source domain has been independently acquired, validated, and documented.
