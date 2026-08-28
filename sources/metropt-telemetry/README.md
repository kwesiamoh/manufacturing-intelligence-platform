# Real equipment telemetry: MetroPT-3

This package provides real industrial equipment telemetry for the standalone MetroPT benchmark. It does not create synthetic telemetry or supply Velora operational facts.

## Source

- Dataset: MetroPT-3 (UCI ID 791)
- DOI: 10.24432/C5VW3R
- License: CC BY 4.0
- Context: compressor Air Production Unit on an operational metro train
- Expected records: 1,516,948
- Documented sensor features: 15

## Acquisition boundary

The 208 MB raw CSV is not distributed in the repository. `ingestion/batch/download_metropt3.py` acquires the official UCI archive in an internet-enabled environment, verifies it against the recorded reproducibility hash, extracts the raw CSV unchanged, and writes an acquisition manifest containing checksums.

## Workflow

1. Install dependencies:

   `python -m pip install -r ..\..\requirements.txt`

2. Acquire Bronze source:

   `python ingestion/batch/download_metropt3.py`

3. Validate the untouched raw source:

   `python pipelines/validate_metropt3.py`

4. Convert incrementally to Silver Parquet:

   `python pipelines/transform_metropt3.py`

The transformation reads the CSV in chunks so the entire source does not need to be loaded into RAM at once.

## Provenance rule

The four rows in `data/bronze/metropt3/reference/failure_windows.csv` reproduce the failure-window metadata shown on the UCI MetroPT-3 dataset page. They are reference metadata, not generated failures. The sensor dictionary is likewise based on UCI's published variable descriptions.

MetroPT is a source-qualified external benchmark and is not row-level joined to Steel Energy or the synthetic Velora enterprise.
