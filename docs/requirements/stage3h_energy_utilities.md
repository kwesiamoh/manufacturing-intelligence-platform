# Stage 3H — Enterprise Energy and Utilities

## Grain
Two outputs are generated:

1. line-shift energy:
   one record per Stage 3D production record

2. site-shift energy:
   one record per site and shift

## Relationships
Each line-shift record retains `production_record_id`, so energy can be analyzed against:
- production quantity
- product
- shift
- downtime
- quality
- line class
- site

ERA5-Land temperature is joined only by fictional site and shift time and remains labelled `REAL_EXTERNAL_CONTEXT`.

## Data policy
Enterprise energy values are synthetic integration data.

The Energy Drink Can Line uses a documented synthetic compressed-air design
assumption of `5.0 Nm³/1,000 cans`, applied through the same quantity-based
utility formula used by the other modeled line classes. Published equipment
pneumatic requirements provide external basis context only; the resulting
Velora utility values are not measured plant observations.

They are not relabelled values from:
- Steel Industry Energy Consumption
- Industrial Park IES utilities
- EIA MECS
- ITAC

Those datasets remain real operational/reference/benchmark sources in their original contexts.
