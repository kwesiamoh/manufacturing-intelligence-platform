# Stage 13E.1 — Condition Monitoring Feasibility (fix)

This revision fixes PyArrow Hive-partition inference when telemetry files are
stored under directories such as `sensor_id=TS3`.

The Parquet files already contain a `sensor_id` field. Calling
`pyarrow.parquet.read_table()` on a path beneath a Hive-style partition folder
can cause Arrow to attempt to merge the folder-derived partition field with the
stored field.

The script now reads individual files through `ParquetFile.read()`, avoiding
partition inference.

It also reports direct telemetry-cycle versus condition-label alignment.

Run:

```powershell
python .\scripts\profile_stage13e1_condition_monitoring.py
```
