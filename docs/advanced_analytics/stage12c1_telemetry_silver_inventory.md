# Stage 12C.1 — Telemetry Silver Inventory

The enterprise `fact_telemetry` table is empty, so Stage 12C must use the real
MetroPT telemetry source directly rather than fabricating enterprise telemetry.

This script searches the repository for telemetry/MetroPT/sensor Parquet or CSV
files under:

- `data/silver`
- `sources`

For Parquet files it reports:

- path
- file size
- row count
- row groups
- schema
- likely timestamp coverage

It does **not** print raw telemetry rows.

## Run

From the repository root:

```powershell
python .\scripts\inventory_telemetry_silver.py
```

Send the output back before building the anomaly model. The next model will be
based on the actual MetroPT schema and source provenance.
