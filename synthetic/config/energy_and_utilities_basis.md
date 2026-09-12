# Energy and Utilities Basis

## Purpose
Generate only the minimum fictional-enterprise energy layer required for:
- electricity consumption
- energy intensity
- idle electricity
- weather-normalised/site-context analysis
- PET compressed-air usage

## PET electrical basis
The principal reference is the peer-reviewed study *Energy Consumption of Beverage-Bottling Machines* (Sustainability 2021, 13, 9880).

For the measured PET bottling plant, the study reports:
- average production-period electrical power: 245.3 kW
- average unproductive-period electrical power: 12.327 kW
- the stretch-blow moulder as the dominant consumer

energy and utilities uses these measurements solely as an external anchor and
never attributes them to the fictional sites.

## Can-line basis
The fictional 60,000 cans/hour line uses a 250 kW production design point. This is within a published 120-450 kW load range for commercial can-filling lines rated from 12,000 to 60,000 cans/hour.

It is explicitly synthetic master/operational data.

## Compressed air
PET compressed-air intensities are synthetic design values informed by published PET blow-moulding ranges.

The fictional can line uses `5.0 Nm³/1,000 cans` as a synthetic design
assumption. It is anchored to published canning-equipment pneumatic-demand
specifications from Wild Goose Filling and Cask, which document clean/dry air
requirements ranging from individual filler/seamer demand to total-system demand
including air treatment. Because the published machines have different speeds
and system boundaries, the 5.0 value is a governed design assumption without a
direct-measurement or single-machine extrapolation claim.

The can-line value uses the same generic energy and utilities formula as PET:

`compressed_air_nm3 = intensity × actual_quantity / 1,000`

This is synthetic operational utility data. The manufacturer specifications are
real external basis information; neither is measured Velora plant data.

Primary specification references:

- <https://wildgoosefilling.com/wp-content/uploads/2019/10/WGC-50-Spec-Sheet_2019-Q4.pdf>
- <https://wildgoosefilling.com/products/single-lane-evolution-series>
- <https://www.cask.com/canning-systems/acs-automated-canning-system-v5/>

## Weather
ERA5-Land air temperature remains real external-context data.

A deliberately simple auxiliary-load response is used:
- above 22 C: small cooling-related increase
- below 5 C: small heating/support-load increase

This input supports contextual analytics only; building-energy simulation lies
outside its scope.

## Scope boundary
No steam model, boiler model, process-heat balance, refrigeration thermodynamics, water balance, or detailed compressed-air network simulation is introduced.

Real Industrial Utilities steam/compressed-air data and Industrial Water data
remain separate benchmark and reference sources outside Velora operations.
