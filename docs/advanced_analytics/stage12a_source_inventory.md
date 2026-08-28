# Stage 12A — Advanced Analytics Source Inventory

Stage 11 produced the v1 Power BI reporting layer. Stage 12 now adds selected
advanced analytics without turning the project into a full data-science platform.

## Planned Stage 12 sequence

### 12A — Source inventory and analytics design
Confirm the exact database objects and fields available for analytical modelling.

### 12B — Statistical process control
Use production/quality KPIs for practical SPC monitoring where the data grain
supports it.

### 12C — Anomaly detection
Use the MetroPT telemetry diagnostics and/or curated manufacturing/energy series
for anomaly detection. Existing DQ warnings remain DQ findings and are not
silently reclassified as operational anomalies.

### 12D — Energy anomaly analytics
Identify unusually high energy intensity or idle-energy behaviour relative to
appropriate operational context.

### 12E — Forecasting
Add a limited, portfolio-relevant forecast, most likely production output and/or
energy demand. Avoid forecasting every available metric.

## Scope boundary

Stage 13 remains the dedicated maintenance/reliability stage. MTBF/MTTR and
maintenance-specific reliability modelling should not be pulled forward into
Stage 12 unless needed as supporting context.

## Run

From the repository root:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
  -h localhost -p 5433 -U postgres `
  -d manufacturing_intelligence `
  -f .\sql\validation\600_inventory_stage12_analytics_sources.sql
```

Send the output back before implementing the analytical models. This prevents
us from guessing column names or duplicating analytics that already exist.
