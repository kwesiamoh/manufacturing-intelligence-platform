# Stage 6B utilities and auxiliary-energy KPI definitions

## Why supplemental detail tables are used

The original canonical `fact_energy` table stored the line total electricity needed for Stage 6A.

The Stage 3H Silver files also contain:
- production electricity
- idle electricity
- compressed-air volume
- auxiliary electricity
- weather-sensitive auxiliary load
- real ERA5-Land temperature context

Stage 6B preserves these already-existing fields in two PostgreSQL detail tables rather than fabricating missing utilities.

## Line production electricity

Electricity attributed to operation of the production line while producing.

## Line idle electricity

Electricity attributed to the line's idle-load component.

## Idle energy share

`Line Idle Electricity / Line Total Electricity`

This measures the fraction of line electrical energy associated with the Stage 3H idle-load model.

It is not equivalent to downtime percentage.

## Site auxiliary electricity

Electricity associated with the site's modeled auxiliary base load plus weather-sensitive auxiliary load.

## Auxiliary energy share

`Site Auxiliary Electricity / Site Total Electricity`

where:

`Site Total Electricity = Sum of Line Electricity + Site Auxiliary Electricity`

## Weather-sensitive auxiliary load

The site model contains:
- fixed auxiliary base kW
- weather-sensitive auxiliary kW

ERA5-Land temperature is real external context. The resulting site auxiliary electricity remains part of the synthetic enterprise integration model.

This distinction must remain visible in documentation and dashboards.

## Compressed air

`compressed_air_nm3` is present where Stage 3H models a line-class intensity.

PET line classes retain their existing synthetic compressed-air assumptions.
`CAN_ENERGY_250` uses a separate synthetic canning-line design assumption of
`5.0 Nm³/1,000 cans`; it does not reuse a PET blow-moulding value.

Therefore:
- null = not modeled / not applicable under the current model for a future or
  unsupported line class
- zero = a real modeled value of zero

These meanings must not be conflated.

## Compressed-air intensity

`Compressed Air Nm3 / Actual Units × 1,000`

It is calculated only from records with a modeled compressed-air value.

For the can line, `Compressed Air Nm³ = 5.0 × Actual Cans / 1,000` for
positive-production rows. This is synthetic operational utility data, not a
measured Velora plant KPI.

## Real external utility datasets

The Zenodo industrial-park steam/compressed-air dataset and Statistics Canada water survey remain real reference/benchmark datasets.

They are not joined to the fictional beverage sites as if they were site measurements.

## Utilities not synthesized

No new:
- steam
- water
- natural gas
- chilled-water consumption

is created in Stage 6B merely to populate the dashboard.

This preserves the project's real-data-first and provenance rules.
