# Stage 3I — Financial Reference Parameters

## Purpose
Define the minimum financial assumptions required later for production-loss and maintenance-cost calculations.

## Scope
This stage defines parameters only. It does not calculate:
- downtime loss cost
- quality loss cost
- maintenance cost
- energy cost
- total improvement opportunity
- business-case savings

Those calculations belong to the later production-loss and energy analytics stages.

## Product loss values
Each product has a synthetic internal `standard_loss_value` expressed in EUR per unit.

These values are:
- fictional enterprise planning assumptions;
- not retail prices;
- not claimed market prices;
- not copied from the real public datasets.

They exist only so later lost-output and reject quantities can be translated into a consistent financial impact.

## Maintenance labor
A single enterprise standard burdened labor rate of EUR 42 per labor hour is used.

Using one internal rate avoids adding unsupported country-specific labor-market assumptions.

Material, spare-parts and other maintenance costs remain null unless the later analytics scope genuinely requires them.

## Energy prices
No synthetic electricity or gas tariff is created here.

The project already contains real Eurostat non-household electricity and gas price data. Energy-cost analytics will use valid country/period mappings from that real benchmark source later.

## Currency
EUR is the reporting currency for the fictional six-site European enterprise.

## Data classification
All values in this package are `SYNTHETIC_REFERENCE`.
