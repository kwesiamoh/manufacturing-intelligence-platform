# Stage 6A energy KPI definitions

## Electricity consumption

`electricity_kwh`

Total line electricity consumed during the shift.

The value is loaded from the Stage 3H synthetic enterprise energy model and stored in `fact_energy`.

## Average demand

`avg_demand_kw`

Average electrical demand over the shift.

It is not peak demand.

## Energy intensity per 1,000 actual units

`Electricity kWh / Actual Quantity × 1,000`

This measures the electricity required per thousand units produced, including rejected units.

## Energy intensity per 1,000 good units

`Electricity kWh / Good Quantity × 1,000`

This is the preferred production-energy KPI for enterprise benchmarking because it relates energy consumption to usable output.

A line with identical energy consumption but more rejected product will therefore have a worse good-unit energy intensity.

## Electricity per operating hour

`Electricity kWh / Operating Hours`

This expresses electricity consumption relative to actual run time.

It should not be interpreted as a measured instantaneous power peak.

## Electricity per planned hour

`Electricity kWh / Planned Production Hours`

This expresses total shift electricity over the scheduled production window.

## Ranking direction

For energy intensity:

**lower is better**

Lines and sites are therefore ranked ascending by `kwh_per_1000_good_units`.

## Aggregation

Intensity is always recalculated from aggregated numerator and denominator:

`SUM(kWh) / SUM(good units)`

The system does not average individual shift intensities to produce site or line totals. This avoids weighting small and large production periods equally.

## Scope boundary

Stage 6A covers electricity performance only.

It does not yet:
- assign electricity tariffs or costs;
- calculate utility costs;
- calculate compressed-air intensity;
- calculate water or steam intensity;
- detect anomalous energy behavior;
- create Power BI dashboards.

Those belong to later Stage 6 steps.
