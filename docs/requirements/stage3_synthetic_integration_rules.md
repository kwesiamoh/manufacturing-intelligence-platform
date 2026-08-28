# Stage 3 Synthetic Integration Rules

## Enterprise context
The fictional enterprise is one multinational beverage manufacturer with six European sites and 30 production lines.

## Product rule
All fictional enterprise products must belong to one coherent beverage portfolio. Site and line assignments may differ, but no site may be assigned unrelated industrial products such as automotive parts, semiconductor wafers, hydraulic components, or university-facility assets.

## Real-data rule
Real public datasets retain their original source identities and industrial context.

Examples:
- beverage production/downtime: operational anchor
- MetroPT-3 compressor telemetry: real compressor reference/behavior source
- SECOM: semiconductor quality/process reference
- hydraulic condition monitoring: reliability reference
- FMUCD: maintenance benchmark/reference
- CNC series production: production/changeover reference
- ITAC: energy opportunity benchmark
- industrial park utilities: utility behavior/reference
- StatCan water: water benchmark
- EIA MECS: energy/fuel benchmark
- EU ETS: emissions benchmark
- Eurostat prices: energy-price benchmark
- ERA5-Land: real external weather context

## Synthetic-data rule
Synthetic data may only be created where the enterprise demonstration needs relationships that no real source can provide, such as:
- site-to-line-to-product assignments
- production plans
- line capacities
- beverage equipment hierarchy
- maintenance events tied to beverage equipment
- beverage-relevant quality events
- enterprise energy/utility allocation
- financial loss parameters

Every such field or record must be marked `SYNTHETIC_INTEGRATION`, `SYNTHETIC_MASTER_DATA`, `SYNTHETIC_OPERATIONAL`, or `SYNTHETIC_REFERENCE` as appropriate.

## Null-before-invention rule
If a field is not required for a KPI, relationship, dashboard, or business case, leave it null or omit it rather than inventing a value.

## Scope rule
Do not add new operational domains beyond those in the original project brief.
