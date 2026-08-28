# Stage 13C — Failure Mode and Downtime Analysis

This stage separates three populations:

1. all downtime events;
2. unplanned downtime events;
3. corrective-maintenance-linked failure events.

The distinction matters because not every downtime event is an independent
equipment failure.

## Views

### `analytics.vw_failure_reason_downtime_summary`

Provides site/failure-reason metrics including:

- downtime event count;
- unplanned downtime event count;
- corrective-linked failure count;
- total downtime;
- unplanned downtime;
- corrective-linked downtime;
- production loss;
- average unplanned event duration;
- site-level Pareto rank;
- downtime share and cumulative share.

### `analytics.vw_equipment_failure_burden`

Ranks equipment by:

- corrective failure frequency;
- corrective downtime burden;
- MTTR;
- MTBF proxy;
- corrective maintenance cost;
- linked production loss.

## Provenance

The event layer is `SYNTHETIC_ENTERPRISE`. Results are workflow demonstrations,
not measured beverage-plant reliability evidence.

## Run

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
  -h localhost -p 5433 -U postgres `
  -d manufacturing_intelligence `
  -f .\sql\analytics\730_create_stage13c_failure_downtime_analysis.sql
```

Then:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
  -h localhost -p 5433 -U postgres `
  -d manufacturing_intelligence `
  -f .\sql\validation\731_validate_stage13c_failure_downtime_analysis.sql
```
