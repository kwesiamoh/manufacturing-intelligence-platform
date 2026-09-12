# Maintenance work orders, labour, and cost

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
FMUCD contains real CMMS records from university facilities. Its value here is
the large-scale coverage of work-order timing, planned and unplanned
maintenance, labour hours, and maintenance costs. The facilities provenance
must remain explicit; beverage-manufacturing labels would misrepresent the
source.

For the manufacturing intelligence platform, this dataset supports:
1. exercise large-scale maintenance ingestion and transformation;
2. build generic work-order/cost data models;
3. benchmark realistic missingness and cost/labour distributions;
4. inform synthetic manufacturing-specific work-order calibration only when that use is explicitly documented and kept separate from the real source records.

Direct joins to the separate real bottling-line production and downtime dataset
are outside the supported integration.

## Layering
- `bronze/`: original downloaded CSV, unchanged.
- `silver/`: normalized Parquet output generated from Bronze.
- `schema/`: source-to-Silver field mapping.
- `provenance/`: source and licensing metadata.
- `scripts/`: reproducible download, validation and transformation scripts.

No synthetic maintenance records are included in this package.
