# Stage 12A.2 — Analytics Feasibility Profile

The Stage 12A schema inventory established that the required production,
quality, energy, and telemetry objects exist.

Before selecting analytical methods, this read-only profile checks whether the
candidate fields contain enough usable observations.

## What the profile determines

- whether `fact_quality.measurement_value` and specification limits are populated
  enough for measurement-based SPC;
- whether `fact_telemetry` is populated and has usable sensor/equipment coverage;
- whether production and energy facts have sufficient time-series continuity;
- which source dataset IDs contribute to each candidate analytical domain;
- the schema of `dim_source_dataset` so provenance can be explicitly documented
  in the subsequent analytics stage.

## Decision logic after the profile

- If quality measurements + limits are well populated, use measurement-based SPC.
- If they are sparse, use a statistically appropriate attribute chart on reject
  proportions instead of pretending continuous measurements exist.
- If telemetry is populated, develop a separate operational anomaly model.
- If telemetry is not populated in PostgreSQL, keep the validated MetroPT
  diagnostics as external analytical evidence and decide whether to load a
  curated telemetry analytical subset rather than forcing the full raw dataset
  into the enterprise fact model.
- Forecasting will use the curated production/energy grains, which already have
  confirmed 2024–2025 coverage.

No database objects are changed by this script.
