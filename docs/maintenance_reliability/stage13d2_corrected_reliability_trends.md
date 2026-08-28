# Stage 13D.2 — Corrected Reliability Trends

## Correction

The original Stage 13D grouped corrective failures by raw downtime
`event_start`.

Fourteen corrective events occurred between 00:34 and 05:34 on 2026-01-01.
Direct inspection confirmed that all 14 link to production records whose shift
started at 22:00 on 2025-12-31 and whose production `date_id` is 20251231.

These events therefore belong to the 2025-12-31 operating period used by the
line operating-hours denominator.

Stage 13D.2 attributes each corrective event to the **linked production shift
date** rather than the raw downtime timestamp.

Stage 16A.6 preserves this attribution and hardens its lineage. Monthly trends
now consume one row per source-qualified downtime failure event. The linked
production lookup uses both the downtime source dataset and production record
ID. Additional maintenance work orders can change repair-duration measures but
cannot multiply the event count or downtime duration.

The two accepted monthly view schemas are unchanged and are replaced in place,
so the existing `gold_bi` Power BI compatibility views retain their dependencies.

## Resulting reporting rule

Failure month:

`month(linked production record calendar_date)`

Operating-hours month:

`month(production record calendar_date)`

This keeps event attribution and operating exposure on the same operational
calendar.

## Expected validation

- 24 months
- 2024-01 through 2025-12
- 30 lines
- 720 site-line-month rows
- 46,670 corrective failures
- no artificial 2026-01 trend bucket

The MTBF value remains an operating-hours proxy because line operating hours,
not direct equipment runtime, form the exposure denominator.

## Run

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
  -h localhost -p 5433 -U postgres `
  -d manufacturing_intelligence `
  -f .\sql\analytics\742_create_stage13d2_corrected_reliability_trends.sql
```

Then:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
  -h localhost -p 5433 -U postgres `
  -d manufacturing_intelligence `
  -f .\sql\validation\743_validate_stage13d2_corrected_reliability_trends.sql
```
