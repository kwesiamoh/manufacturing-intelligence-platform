# Step 3 — Real Manufacturing Process / Quality Data

Source: UCI Machine Learning Repository, SECOM dataset (McCann & Johnston, 2008).
DOI: 10.24432/C54305
License: CC BY 4.0.

Purpose in the manufacturing-intelligence project:
- real semiconductor manufacturing process measurements
- pass/fail yield label
- timestamped production-entity observations
- missing-value and feature-quality analysis

This package does not fabricate production records. Raw UCI files belong in `bronze/secom/` and are transformed into a Silver Parquet dataset only after validation.

## Expected raw files

- `secom.data`
- `secom_labels.data`
- `secom.names`

The authoritative UCI page reports 1,567 instances and 591 features in its metadata. In the public raw file, users commonly load 590 anonymous sensor columns from `secom.data`, while the pass/fail label and timestamp are stored separately in `secom_labels.data`. The validation script records the observed structure rather than silently forcing the metadata count.

## Workflow

1. `python scripts/download_source.py`
2. `python scripts/validate_bronze.py`
3. `python scripts/build_silver.py`

The downloader first tries the current UCI archive and legacy UCI file URLs. It does not silently replace the source with synthetic data.

`build_silver.py` is the canonical Silver contract because it produces the
integration-safe `sample_id`, parsed `event_timestamp`, source `raw_label`, and
`quality_result` fields documented in `metadata/quality_domain_mapping.md`.
Its outputs are `secom_process_quality.parquet` and
`secom_quality_events.parquet`.

`scripts/bronze_to_silver.py` and its retained `secom_quality.parquet` output
are superseded historical artifacts. They are not deleted, but the source
runner does not execute that competing contract.
