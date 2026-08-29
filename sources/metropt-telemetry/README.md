# Real equipment telemetry: MetroPT-3

This package provides real industrial compressor telemetry for anomaly,
fault-event, and predictive-warning evaluation. Original records remain
external UCI data. A downstream workflow creates a separately governed
MetroPT-informed synthetic enterprise compressor-maintenance scenario; it does
not turn the source observations into Velora operational telemetry.

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

5. Reproduce the accepted anomaly score and adaptive alert policy from the
   repository root:

   `python scripts/run_metropt_anomaly_scoring.py`

   `python scripts/select_metropt_alert_policy.py`

6. Evaluate real 2-, 4-, and 6-hour warnings and create the governed enterprise
   compressor adaptation:

   `python scripts/run_metropt_predictive_maintenance.py`

The enterprise output is
`data/silver/synthetic_enterprise/telemetry/metropt_enterprise_telemetry.parquet`.
It maps to the existing `SITE-DE-01-U-AIR-01` compressed-air asset, retains the
original timestamp in `source_event_timestamp`, and identifies the controlled
degradation signal as `SYNTHETIC_CONTROLLED`.

The materialized enterprise output is a canonical PostgreSQL build input and
participates in enterprise DQ through completeness, uniqueness, equipment
mapping, lineage, and cadence checks. The source-model workflow above remains
the optional regeneration route. Original source faults and analytical warning
states are not treated as data-quality defects.

## Provenance rule

The four rows in `data/bronze/metropt3/reference/failure_windows.csv` reproduce the failure-window metadata shown on the UCI MetroPT-3 dataset page. They are reference metadata, not generated failures. The sensor dictionary is likewise based on UCI's published variable descriptions.

MetroPT is not row-level joined to unrelated source datasets. PostgreSQL Gold
views integrate only the governed compressor adaptation with enterprise
site/equipment dimensions and optional maintenance-work-order context. Real and
synthetic evaluation scopes remain distinct, and the current Power BI report
does not contain the predictive-maintenance outputs.
