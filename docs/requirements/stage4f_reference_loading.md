# Stage 4F — Reference and Benchmark Loading

## Purpose
Load selected real benchmark/reference datasets into PostgreSQL without falsely joining them to the fictional beverage enterprise.

## Loaded
- ITAC assessments
- ITAC recommendations
- FMUCD maintenance benchmark
- Statistics Canada industrial water
- EIA MECS fuel/energy benchmark tables
- EU ETS emissions
- Eurostat energy-price Silver outputs

## Why separate `ref_*` tables?
The real public datasets come from different organizations, industries and geographies.

Loading them into dedicated reference tables preserves:
- source provenance
- original row structure
- benchmark/reference role
- separation from fictional operational facts

## JSONB design
Stage 4F stores each original standardized Silver row in PostgreSQL `JSONB`.

This is intentional:
- the source datasets have very different schemas;
- we do not need to redesign every benchmark dataset into a full relational model;
- later analytics can extract only the fields needed for specific benchmark marts.

This avoids unnecessary scope expansion.

## Not loaded in Stage 4F
Large operational/reference sensor datasets such as MetroPT-3, SECOM and hydraulic condition monitoring remain in Parquet for Python analytics.

They do not need to be copied wholesale into PostgreSQL merely to demonstrate the project architecture.

## Scope boundary
Stage 4F is a reference-store step, not Gold modelling.
