# Stage 4D/4E — Synthetic Fact Loading

## Necessary schema alignment
The original Stage 2 fact schema captured source provenance but did not yet preserve the Stage 3 cross-fact lineage identifiers.

Before loading, Stage 4D adds only these lineage columns:
- `source_record_id`
- `production_record_id` where needed
- `downtime_event_id` for maintenance
- `downtime_source_dataset_id` for the source of the downtime event referenced
  by maintenance

This preserves the already-defined relationships:
- production -> downtime
- production -> quality
- downtime -> maintenance
- production -> energy

No new business domain is introduced.

Migration 005 makes the downtime reference source explicit. The Velora loader
sets it deterministically to `SYNTHETIC_ENTERPRISE`, because both sides of the
generated relationship belong to that integration source. Reliability SQL joins
on the source ID plus textual event ID; it does not assume event IDs are globally
unique.

## Loaded facts
- fact_production
- fact_downtime
- fact_quality
- fact_maintenance
- fact_energy

## Not loaded yet
- telemetry
- utility measurements
- water benchmarks
- emissions benchmarks
- energy-price benchmarks
- production-order reference data
- weather-context fact
- data-quality fact

Those remain later Stage 4 loads.

## Reload behavior
The loader deletes only existing `SYNTHETIC_ENTERPRISE` rows from the five target fact tables before reloading. Real/reference source rows are untouched.

## Validation
The loader checks:
- exact expected row counts
- downtime -> production lineage
- quality -> production lineage
- maintenance -> downtime lineage
- energy -> production lineage
