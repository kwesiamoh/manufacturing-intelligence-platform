# Stage 5A KPI definitions

## Availability

Availability is calculated as:

`Operating Time / Planned Production Time`

This project uses the shift-level planned production window already stored in `fact_production`.

## Performance

Performance is calculated as:

`Actual Quantity / (Operating Time × Nominal Rate)`

where nominal rate is expressed in units per hour and operating time is converted from minutes to hours.

This measures reduced-speed loss while the line is operating.

## Quality

Quality is calculated as:

`Good Quantity / Actual Quantity`

## OEE

OEE is calculated as:

`Availability × Performance × Quality`

The three components are calculated from the validated production facts rather than using precomputed synthetic latent factors.

## Production attainment

`Actual Quantity / Planned Quantity`

This answers whether the shift met its production plan.

## Good-output attainment

`Good Quantity / Planned Quantity`

This is stricter than production attainment because rejected units do not count as delivered good output.

## Throughput

Two throughput measures are provided:

- running throughput = actual units / operating hours
- scheduled throughput = actual units / planned production hours

## Reject rate

`Reject Quantity / Actual Quantity`

## Production loss measures

Stage 5A creates unit-equivalent loss measures:

- planned downtime loss units
- unplanned downtime loss units
- changeover loss units
- speed loss units
- quality loss units

Downtime loss units convert downtime minutes into theoretical units using the shift's nominal production rate.

Speed loss units are:

`Theoretical output during operating time - Actual Quantity`

Quality loss units equal rejected units.

## Important interpretation

The individual loss categories should not automatically be summed and interpreted as an exact accounting bridge to `planned_quantity - good_quantity`, because the production plan and nominal technical capacity are different baselines.

Stage 5B will build the formal loss-accounting bridge and financial translation using an explicitly chosen baseline.
