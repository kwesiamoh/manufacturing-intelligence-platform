# Stage 13A.2 — Reliability KPI Feasibility and Provenance

This read-only profile determines whether MTBF, MTTR, availability, and
maintenance-burden KPIs can be calculated defensibly from the enterprise event
layer.

It checks:

- source-dataset provenance of maintenance, downtime, and equipment records;
- event time coverage;
- null/completeness levels;
- planned versus unplanned event counts;
- duration sanity;
- maintenance types;
- equipment coverage;
- maintenance-to-downtime linkage.

## Reliability KPI rule

MTBF will only be calculated from a clearly defined failure-event population,
normally unplanned downtime/failure events, and only where a defensible
operating-time denominator is available.

MTTR will only be calculated from actual repair/maintenance durations associated
with failure events. It will not be inferred from arbitrary planned maintenance
records.

No assumption is made that the real `FMUCD` benchmark or `HYDRAULIC_CM`
condition-monitoring source represents beverage-plant operational history.

## Run

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
  -h localhost -p 5433 -U postgres `
  -d manufacturing_intelligence `
  -f .\sql\validation\710_profile_stage13_reliability_feasibility.sql
```
