# Stage 4G — Local Database Validation

This stage validates the PostgreSQL implementation before a repeatable pipeline runner is added.

Checks include:
- expected dimension counts
- expected synthetic operational fact counts
- expected reference-store counts
- production/downtime/quality/maintenance/energy lineage
- quantity reconciliation
- timestamp and duration sanity
- positive energy consumption/demand
- duplicate source-record protection through the existing unique indexes

The Stage 4G Python validator exits with a non-zero code if any required check fails.

`dim_sensor = 0` is intentional at this stage.
`ref_eurostat_energy_price` must be non-empty. Its exact count is not fixed
because the generic reference loader loads every governed Silver Parquet under
the Step 14 package, including metadata and expanded observation artifacts.
