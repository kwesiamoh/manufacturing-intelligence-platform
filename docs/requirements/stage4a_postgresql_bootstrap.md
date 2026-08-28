# Stage 4A — PostgreSQL Bootstrap

## Purpose
Create the configured local PostgreSQL database and execute the canonical
Stage 16A.2 Velora operational build.

## Scope
`pipelines/postgres/bootstrap_database.ps1` now implements the complete
dependency-ordered build defined in
`docs/reproducibility/canonical_build_order.md`. It preflights governed inputs,
applies all required schema/migration/configuration SQL, runs the required
loaders, creates accepted operational analytics and BI views, and executes the
canonical validation queries.

Optional MetroPT and hydraulic benchmark reproduction is excluded.

## Prerequisites
- PostgreSQL installed locally
- `psql` available in the Windows PATH
- Python dependencies from `pipelines/postgres/requirements-stage4.txt`
- governed/materialized inputs listed in the canonical build-order document

## Database
Default: `manufacturing_intelligence` on `localhost:5433` as user `postgres`.
Host, port, database, administrative database, and user are configurable runner
parameters.

The canonical tables remain in PostgreSQL's `public` schema for this portfolio project. A multi-schema warehouse layout is unnecessary at this stage.
