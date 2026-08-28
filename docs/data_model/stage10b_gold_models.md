# Stage 10B final Gold analytical models

Stage 10B creates the curated PostgreSQL Gold layer that will be used as the primary source for the Power BI stage.

The design deliberately keeps the number of Gold objects small. Existing Stage 5, Stage 6 and Stage 7 views remain the detailed analytical foundation; Gold consolidates those views into stable reporting grains.

## Gold schema

`gold`

## Models

### `gold.vw_shift_manufacturing_performance`

Grain: one production record / line / shift.

Combines production KPIs, OEE, downtime and loss accounting, financial opportunity estimates, line electricity, idle energy, compressed air and weather-related auxiliary context.

Expected rows: 65,790.

### `gold.vw_line_daily_performance`

Grain: one line per day.

Combines daily production/OEE, technical and financial losses, and electricity KPIs.

Expected rows: 21,930.

### `gold.vw_site_daily_performance`

Grain: one site per day.

Combines daily production/OEE, losses, line electricity and site auxiliary electricity. Site auxiliary shift records are aggregated to site-day before joining, preventing grain multiplication.

Expected rows: 4,386.

### `gold.vw_site_executive_summary`

Grain: one site.

Combines production rankings, technical loss opportunity, total/auxiliary energy performance and external Eurostat electricity-cost benchmarking.

Expected rows: 6.

The electricity cost fields remain benchmark estimates, not invoice or booked cost.

### `gold.vw_data_quality_domain_summary`

Grain: one DQ domain.

Expected rows: 7.

### `gold.vw_data_quality_rule_status`

Grain: one latest DQ rule.

Expected rows: 30.

Telemetry WARN results remain diagnostic findings and are not converted into failures.

## Why views

Gold is implemented as PostgreSQL views rather than duplicated physical tables because the underlying analytical views are already validated, the current portfolio data volume is moderate, and the views keep refresh logic simple and reproducible. Power BI can consume these views directly in the next stage.

## Run

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
  -h localhost -p 5433 -U postgres `
  -d manufacturing_intelligence `
  -f .\sql\analytics\400_create_gold_models.sql
```

Then validate:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
  -h localhost -p 5433 -U postgres `
  -d manufacturing_intelligence `
  -f .\sql\validation\410_validate_gold_models.sql
```
