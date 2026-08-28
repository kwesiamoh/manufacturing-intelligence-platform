# Manufacturing KPI definitions

## Production and OEE

All ratios guard against zero denominators. Aggregated ratios are recalculated
from aggregated numerators and denominators rather than averaging row-level
percentages.

| KPI | Definition |
|---|---|
| Availability | Operating time / planned production time |
| Performance | Actual quantity / (operating hours × nominal units/hour) |
| Quality | Good quantity / actual quantity |
| OEE | Availability × performance × quality |
| Production attainment | Actual quantity / planned quantity |
| Good-output attainment | Good quantity / planned quantity |
| Reject rate | Reject quantity / actual quantity |
| Running throughput | Actual quantity / operating hours |
| Scheduled throughput | Actual quantity / planned production hours |

## Technical loss accounting

The formal loss bridge uses technical capacity rather than the production plan:

```text
Theoretical capacity = planned production hours × nominal rate
Operating capacity   = operating hours × nominal rate
Technical gap        = theoretical capacity - good quantity
Technical gap        = availability loss + performance loss + quality loss
```

- Availability loss is theoretical capacity minus operating capacity and is
  split into mutually exclusive planned and unplanned downtime components.
- Changeover is a subset of planned downtime and is never added a second time.
- Performance loss is operating capacity minus actual quantity.
- Quality loss is actual quantity minus good quantity.
- Plan shortfall is `max(planned quantity - good quantity, 0)` and remains
  separate because the production plan is not the OEE technical baseline.

The synthetic product unit values translate technical loss into
`opportunity_eur`. They are not retail prices, audited margins, booked losses,
or realized savings.

## Electricity and utilities

| KPI | Definition / interpretation |
|---|---|
| Line total electricity | Production electricity + idle electricity |
| Idle energy share | Line idle electricity / line total electricity |
| Site total electricity | Sum of line electricity + site auxiliary electricity |
| Auxiliary energy share | Site auxiliary electricity / site total electricity |
| Electricity intensity | Electricity kWh / output × 1,000 |
| Compressed-air intensity | Compressed air Nm³ / actual units × 1,000 |

Electricity intensity is lower-is-better. Site and line values use summed energy
and summed output, avoiding an unweighted average of shift intensities.

Average demand is not peak demand. Idle energy share is not downtime
percentage. ERA5-Land temperature is real external context, while the resulting
site auxiliary electricity remains synthetic enterprise data.

PET compressed-air values use governed synthetic line-class assumptions. The
CAN line uses exactly **5.0 Nm³/1,000 cans** for positive-production rows. A null
compressed-air value means not modelled/not applicable; it is not equivalent to
zero.

## Electricity-cost benchmark

The benchmark combines synthetic Velora electricity consumption with real
Eurostat `nrg_pc_205` prices:

```text
Benchmark electricity cost = site electricity kWh × benchmark EUR/kWh
Benchmark cost intensity    = benchmark cost EUR / production units × 1,000
```

The accepted band is `MWH2000-19999`, and the accepted tax basis is `X_VAT`.
January–June maps to semester `S1`; July–December maps to `S2` in the same year.
The result is a comparable benchmark, not a site invoice or contracted tariff.

## Reliability

- A corrective failure is counted once at source-qualified downtime-event grain.
- Corrective repair hours remain at maintenance/work-order grain.
- `MTTR = total corrective repair hours / corrective failures`.
- The operating-hours MTBF proxy divides operating exposure by failures; it is
  not elapsed calendar time between failures.
- Corrective downtime ratio divides linked corrective downtime by operating
  exposure.
- Monthly trends attribute the failure to its linked production shift
  date so numerator and exposure use the same operating calendar.

The accepted lineage checks found zero ambiguous source-qualified links and zero
downtime multiplication.

## Data quality

Rule results retain `PASS`, `WARN`, and `FAIL` semantics. Mandatory `FAIL`
results stop the canonical build; legitimate `WARN` results remain nonfatal.
The accepted proof contains 24 PASS, 0 WARN, and 0 FAIL for the canonical Velora
rules. Optional external benchmark rules do not change that operational score.

## Field-level reference

The complete field catalog is available in
[`canonical_data_dictionary.csv`](../data_dictionary/canonical_data_dictionary.csv).
