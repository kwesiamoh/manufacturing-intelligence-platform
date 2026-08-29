# European non-household electricity and gas price benchmark

## Domain
European electricity and natural-gas prices for non-household consumers.

## Authoritative source
Eurostat.

Datasets:
- `nrg_pc_205` — Electricity prices for non-household consumers, bi-annual data
- `nrg_pc_203` — Gas prices for non-household consumers, bi-annual data

## Dataset reference
For the second half of 2025:
- EU average non-household electricity price for Band IC (500–2,000 MWh/year): €18.37 per 100 kWh.
- EU average non-household gas price for Band I3 (10,000–100,000 GJ/year): €6.05 per 100 kWh.

These are benchmark statistics, not plant bills.

## Project use
Use for:
- European industrial energy-price benchmarks;
- financial opportunity modelling;
- sensitivity analysis by country and consumption band;
- comparison with U.S. MECS energy prices.

Do not:
- assign these averages directly to a fictional site without an explicit tariff assumption;
- treat them as hourly market prices;
- infer site-level invoices or taxes from a single EU average;
- join them row-by-row to unrelated plant telemetry.

No synthetic records are included.

## Canonical workflow

The accepted electricity-price route is explicit and repository-relative:

1. `pipelines/bronze/download_eurostat_nrg_pc_205.py`
2. `pipelines/bronze/validate_eurostat_nrg_pc_205.py`
3. `pipelines/silver/expand_eurostat_nrg_pc_205.py`

It retains the official JSON-stat response, validates required dimensions and
observations, and produces both the decoded observation table and the focused
six-country 2024-2025 Parquet consumed by the accepted PostgreSQL loader.

No competing metadata-only transformation route is included in the public
package.
