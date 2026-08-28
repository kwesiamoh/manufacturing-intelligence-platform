# Step 6 — Maintenance Work Orders, Labour and Cost

This package adds a **real maintenance work-order reference domain** using the Facility Management Unified Classification Database (FMUCD), published on Mendeley Data.

## Source
- Dataset: Facility Management Unified Classification Database (FMUCD)
- Authors: Ashish Kumar Pampana, JungHo Jeon, Soojin Yoon, Theodore Weidner
- Version: 1
- DOI: 10.17632/cb8d2nsjss.1
- Published: 2024-03-28
- Licence: CC BY 4.0
- Source page: https://data.mendeley.com/datasets/cb8d2nsjss/1
- Raw format: CSV
- Reported raw size: ~1.34 GB

## Important scope note
FMUCD is real CMMS data from university facilities, not a manufacturing production plant. It is retained because it provides genuine work-order timing, planned/unplanned maintenance, labour hours, and maintenance cost fields at large scale. It must **not** be relabelled as beverage-manufacturing work orders.

For the manufacturing intelligence platform, this dataset is used to:
1. exercise large-scale maintenance ingestion and transformation;
2. build generic work-order/cost data models;
3. benchmark realistic missingness and cost/labour distributions;
4. calibrate later synthetic manufacturing-specific work orders only if no directly suitable public manufacturing CMMS dataset can be obtained.

It is not joined directly to the real bottling-line dataset from Step 5.

## Layering
- `bronze/`: original downloaded CSV, unchanged.
- `silver/`: normalized Parquet output generated from Bronze.
- `schema/`: source-to-Silver field mapping.
- `provenance/`: source and licensing metadata.
- `scripts/`: reproducible download, validation and transformation scripts.

No synthetic maintenance records are included in this package.
