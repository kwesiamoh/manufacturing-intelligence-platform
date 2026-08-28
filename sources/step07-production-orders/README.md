# Step 7 — Real production-order/changeover context

This package adds a real industrial series-production dataset to the manufacturing intelligence project.

## Authoritative source

- Dataset: **Series production data set for 5-axis CNC milling**
- Authors: Anna-Maria Schmitt; Bastian Engelmann
- Repository: Zenodo
- DOI: `10.5281/zenodo.10853254`
- Data paper: *A Series Production Data Set for Five-Axis CNC Milling*, Data 2024, 9(5), 66
- Data paper DOI: `10.3390/data9050066`
- License: **CC BY 4.0**

The dataset was recorded on a HERMLE C600 U five-axis milling machine at Pabst Komponentenfertigung GmbH in Schweinfurt, Germany during normal industrial production. It contains 13 recorded series-production sessions between November 2021 and April 2022. Each session covers a changeover into a new anonymized product and the subsequent production period. The products were bearing components from the aerospace domain.

## What is real here

The source provides real industrial timestamps, NC variables, production/changeover labels, anonymized old/new product identifiers, and session durations. The 13 CSV files together contain 190,046 rows according to the data descriptor.

## Important limitation

The source states that the sessions correspond to real customer/series orders, but the public dataset does **not** expose ERP production-order IDs, customer identities, planned quantities, due dates, routings, BOMs, or financial values. This package therefore does not invent those fields.

Later, if the integrated enterprise model requires those unavailable fields, they must be added in a clearly separated synthetic integration layer rather than represented as source data.

## Folder structure

- `bronze/series_production_cnc/` — destination for the 13 original Zenodo CSV files
- `silver/series_production_cnc/` — destination for Parquet conversion
- `metadata/source_manifest.csv` — official filenames, row counts, sizes, and MD5 values
- `metadata/session_reference.csv` — published session/changeover metadata
- `metadata/provenance.json` — source and licensing record
- `schemas/feature_dictionary.csv` — documented NC features and production labels
- `scripts/download_bronze.py` — downloads original files directly from Zenodo
- `scripts/validate_bronze.py` — checks presence, MD5, row count, and basic schema
- `scripts/bronze_to_silver.py` — converts each original CSV to Parquet without fabricating observations

## Run locally

```bash
python scripts/download_bronze.py
python scripts/validate_bronze.py
python scripts/bronze_to_silver.py
```

Python dependencies:

```bash
pip install pandas pyarrow requests
```
