# Real production and downtime data

This package adds the production/downtime domain to the Manufacturing Intelligence Platform.

## Source

**Industrial Production Time-Series Dataset from a Beverage Bottling Line (2022–2023)**  
Zenodo DOI: `10.5281/zenodo.18146866`  
Dataset record: `https://zenodo.org/records/18146866`  
Source file: `production_raw.xlsx`  
Published: 2026-01-04  
License: CC BY 4.0

The repository description states that the records come from a real industrial filling machine operating under production conditions. Production was counted with photoelectric sensors, product type/discards were identified by a PLC, data were sent through a datalogger and MQTT, and the released dataset contains hourly/daily production plus downtime records.

## Scope

Only the **production and downtime** source domain is handled here. It remains separate from unrelated energy, telemetry, quality, and reliability datasets.

No synthetic production or downtime records are created in this package.

## Bronze

`bronze/production_downtime/production_raw.xlsx`

The Bronze file must remain byte-for-byte identical to the file downloaded from Zenodo. The expected MD5 published by Zenodo is:

`d9c095d5eba8706ac7dda92af63f5c35`

The source workbook is acquired from the official Zenodo record with:

```bash
python scripts/download_source.py
```

on a normal internet-connected machine to retrieve and checksum the official file.

## Silver outputs

After Bronze validation, run:

```bash
python scripts/transform_silver.py
```

Expected outputs:

- `silver/production_downtime/production_hourly.parquet`
- `silver/production_downtime/production_daily.parquet`
- `silver/production_downtime/operation_hourly.parquet`
- `silver/production_downtime/downtime_events.parquet`

`scripts/transform_silver.py` is the canonical transformation. Its typed fields
and filenames match `metadata/silver_schema.yaml` and include explicit
`source_dataset_id` provenance.

The transformation standardizes field names/types and derives timestamp columns from the real date/time values. It does **not** fabricate site IDs, product quantities, downtime reasons, asset IDs, targets, or OEE values that are absent from the source.

## Important limitation

The real source contains downtime timing/duration but not a detailed root-cause taxonomy such as mechanical/electrical/material shortage. Those fields are not inferred. Synthetic Velora downtime causes remain separately labelled and governed.
