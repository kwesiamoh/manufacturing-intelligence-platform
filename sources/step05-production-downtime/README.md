# Step 5 — Real production and downtime data

This package adds the production/downtime domain to the Manufacturing Intelligence Platform.

## Source

**Industrial Production Time-Series Dataset from a Beverage Bottling Line (2022–2023)**  
Zenodo DOI: `10.5281/zenodo.18146866`  
Dataset record: `https://zenodo.org/records/18146866`  
Source file: `production_raw.xlsx`  
Published: 2026-01-04  
License: CC BY 4.0

The repository description states that the records come from a real industrial filling machine operating under production conditions. Production was counted with photoelectric sensors, product type/discards were identified by a PLC, data were sent through a datalogger and MQTT, and the released dataset contains hourly/daily production plus downtime records.

## Scope of this increment

Only the **production and downtime** domain is handled here. It is not yet merged with energy, telemetry, quality, or reliability datasets from earlier steps.

No synthetic production or downtime records are created in this package.

## Bronze

`bronze/production_downtime/production_raw.xlsx`

The Bronze file must remain byte-for-byte identical to the file downloaded from Zenodo. The expected MD5 published by Zenodo is:

`d9c095d5eba8706ac7dda92af63f5c35`

The execution environment used to prepare this package could read the official Zenodo record but could not transfer the binary XLSX. Run:

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
`source_dataset_id` provenance. `scripts/bronze_to_silver.py` is a retained
superseded generic sheet-copy route; its four sheet-named Parquets are
historical and are not executed by the source runner.

The transformation standardizes field names/types and derives timestamp columns from the real date/time values. It does **not** fabricate site IDs, product quantities, downtime reasons, asset IDs, targets, or OEE values that are absent from the source.

## Important limitation

The real source contains downtime timing/duration but not a detailed root-cause taxonomy such as mechanical/electrical/material shortage. Those fields must not be inferred. If later project modules require downtime causes, we will obtain another real source or explicitly create a documented synthetic extension rather than misrepresenting it as measured data.
