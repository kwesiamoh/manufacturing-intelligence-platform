# Stage 13B — Equipment Reliability KPIs

## Provenance

The enterprise maintenance, downtime, and equipment records all originate from
`SYNTHETIC_ENTERPRISE`, the fictional beverage-enterprise integration layer.

These results demonstrate reliability analytics workflow. They are not
presented as measured reliability performance from a real beverage plant.

## Corrective failure and work-order populations

A corrective failure event is one source-qualified unplanned downtime event
with at least one corrective maintenance work order. The relationship satisfies:

`fact_maintenance.downtime_source_dataset_id = fact_downtime.source_dataset_id`

and:

`fact_maintenance.downtime_event_id = fact_downtime.source_record_id`

The accepted snapshot contains 46,670 corrective maintenance rows linked to
46,670 distinct downtime events: 46,670 downtime events have one maintenance
row, 123,738 have none, none have more than one, and the observed maximum is
one. A maintenance row has one scalar downtime reference and therefore cannot
reference multiple downtime events.

The schema does not impose one-work-order-per-downtime uniqueness. Future
sources may legitimately attach multiple work orders to one failure event.
`analytics.vw_corrective_maintenance_downtime_link` preserves work-order grain;
`analytics.vw_corrective_failure_event` aggregates repair measures and preserves
downtime at one row per source-qualified failure event.

This is preferable to treating all 170,408 unplanned downtime events as
independent equipment failures.

## MTTR

MTTR is calculated from corrective maintenance `duration_hours`. Work-order
durations are summed within a failure event before event-weighted averaging, so
multiple work orders contribute repair effort without duplicating downtime.

At equipment level:

`MTTR = total corrective repair duration / corrective failure count`

Because every event represents corrective work, this is a defensible repair
duration metric within the synthetic event model.

## Calendar inter-failure interval

For consecutive corrective failures on the same equipment:

`calendar interval = next failure start - prior failure start`

The view reports mean and median calendar inter-failure hours.

This is not called MTBF because calendar elapsed time includes periods when the
equipment may not have been operating.

## Operating-hours MTBF proxy

For line-linked equipment only:

`operating-hours MTBF proxy = total line operating hours / corrective failures`

This is explicitly labelled a **proxy**. The dataset contains line operating
time, not direct runtime meters for every individual equipment asset.

It should not be interpreted as exact equipment-level MTBF.

## Availability proxy

For equipment with the operating-hours MTBF proxy:

`A_proxy = MTBF_proxy / (MTBF_proxy + MTTR)`

This is a reliability availability proxy based on the same line-exposure
assumption. It is not a measured equipment availability KPI.

## Additional metrics

The view also exposes:

- corrective failure count;
- corrective maintenance work-order count and work orders per failure;
- failures per 1,000 line operating hours;
- linked failure downtime;
- mean downtime per linked failure;
- total corrective repair hours;
- corrective maintenance cost;
- linked production loss;
- equipment type and site/line context.

## Views

- `analytics.vw_corrective_maintenance_downtime_link`
- `analytics.vw_corrective_failure_event`
- `analytics.vw_equipment_reliability_kpi`
- `analytics.vw_equipment_type_reliability_summary`

## Run

Create the views:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
  -h localhost -p 5433 -U postgres `
  -d manufacturing_intelligence `
  -f .\sql\analytics\720_create_stage13b_reliability_kpis.sql
```

Validate:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
  -h localhost -p 5433 -U postgres `
  -d manufacturing_intelligence `
  -f .\sql\validation\721_validate_stage13b_reliability_kpis.sql
```
