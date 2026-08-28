# Stage 13D — Reliability Trends

Stage 13D adds a time dimension to the Stage 13B/13C reliability analysis.

## Monthly line/site trend view

`analytics.vw_monthly_reliability_trend`

Metrics:
- corrective failure count;
- corrective downtime hours;
- MTTR;
- affected equipment count;
- line operating hours;
- failures per 1,000 operating hours;
- monthly operating-hours MTBF proxy;
- corrective-downtime / operating-time ratio.

The MTBF measure remains explicitly labelled a proxy because the denominator is
line operating time rather than individual equipment runtime.

## Monthly equipment-type view

`analytics.vw_monthly_equipment_type_reliability_trend`

Metrics:
- corrective failure count;
- affected equipment;
- downtime hours;
- MTTR;
- average downtime per corrective failure.

## Excluded metrics

Maintenance cost and production-loss metrics are intentionally excluded because
Stage 13C validation showed those fields are not populated for the current
corrective-failure records.

## Provenance

All enterprise event records are from the synthetic integration layer. Trend
results demonstrate the reliability analytics workflow and are not real
beverage-plant performance claims.

## Run

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
  -h localhost -p 5433 -U postgres `
  -d manufacturing_intelligence `
  -f .\sql\analytics\740_create_stage13d_reliability_trends.sql
```

Then:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
  -h localhost -p 5433 -U postgres `
  -d manufacturing_intelligence `
  -f .\sql\validation\741_validate_stage13d_reliability_trends.sql
```
