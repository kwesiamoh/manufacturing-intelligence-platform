# Stage 4H — Repeatable Local Pipeline Runner

## Purpose

Provide one simple local entry point for the already-built Stage 4 loaders and validation.

The runner executes, in order:

1. master-dimension load
2. synthetic operational-fact load
3. real reference/benchmark load
4. Stage 4 database validation

It does not recreate the PostgreSQL server or database. Stage 4A is infrastructure bootstrap and remains a one-time setup step.

## Normal full run

```powershell
powershell -ExecutionPolicy Bypass -File .\pipelines\orchestration\run_stage4_local_pipeline.ps1
```

Default connection:
- host: `localhost`
- port: `5433`
- database: `manufacturing_intelligence`
- user: `postgres`

The underlying scripts prompt for the database password. The password is never written to the repository.

## Faster operational reload

The FMUCD reference table contains more than 3.7 million rows and normally does not need to be reloaded when only the fictional enterprise operational data changes.

Use:

```powershell
powershell -ExecutionPolicy Bypass -File .\pipelines\orchestration\run_stage4_local_pipeline.ps1 -SkipReferenceLoads
```

This still reloads:
- dimensions
- production
- downtime
- quality
- maintenance
- energy
- validation

and leaves the already-loaded real reference tables untouched.

## Scope boundary

This is intentionally a small local orchestrator.

It is not:
- Airflow
- Prefect
- Dagster
- AWS orchestration
- a production scheduler

Automated cloud orchestration belongs to later stages of the project.
