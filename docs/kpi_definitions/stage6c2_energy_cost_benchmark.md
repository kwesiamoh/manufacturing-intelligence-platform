# Stage 6C.2 electricity-cost benchmark methodology

## What is being combined

The cost benchmark combines two different data classes:

1. **Synthetic enterprise consumption**
   - site electricity consumption from Stage 3H;
2. **Real external benchmark price**
   - Eurostat `nrg_pc_205`.

The result is therefore a **benchmark electricity-cost estimate**.

It is not:
- an actual utility invoice;
- a contracted tariff;
- an audited accounting expense;
- a claim that Eurostat measured any fictional site.

## Consumption band

The selected Eurostat band is:

`MWH2000-19999`

meaning annual non-household electricity consumption from 2,000 MWh up to but not including 20,000 MWh.

The Stage 6C.2 validation independently calculates annual electricity consumption for every fictional site and verifies that every site-year falls within this band.

## Tax basis

Selected Eurostat tax code:

`X_VAT`

The corresponding Eurostat price level excludes VAT and other recoverable taxes and levies.

This is used as a comparable non-household benchmark basis across countries.

## Currency and unit

- currency: EUR
- unit: kWh

## Semester mapping

Each synthetic site-energy shift is mapped to:

- January through June -> `S1`
- July through December -> `S2`

for the same calendar year.

## Benchmark electricity cost

`Site Electricity kWh × Eurostat Benchmark EUR/kWh`

## Benchmark cost intensity

`Benchmark Electricity Cost EUR / Production Units × 1,000`

Lower benchmark cost intensity is better.

It reflects both:
- production energy intensity; and
- external country-level price conditions.

It should therefore not be interpreted as a pure measure of plant operational efficiency.
