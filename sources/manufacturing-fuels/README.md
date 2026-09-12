# Real manufacturing fuel, natural gas, and purchased-steam benchmark

## Domain
Manufacturing fuel consumption, purchased natural gas, purchased steam, electricity, prices,
quantities and expenditures.

## Authoritative source
U.S. Energy Information Administration (EIA)
2022 Manufacturing Energy Consumption Survey (MECS)

Official 2022 data page:
https://www.eia.gov/consumption/manufacturing/data/2022/

Methodology:
https://www.eia.gov/consumption/manufacturing/data/2022/index.php?view=methodology

## Release status
Final 2022 MECS results were released on 2026-03-18.

The 2022 MECS sample included approximately 15,000 manufacturing establishments and supports
industry-level estimates for U.S. manufacturing.

## Source tables

- Table 3.1 — Energy Consumption as a Fuel by Manufacturing Industry and Region (physical units)
- Table 7.3 — Average Prices of Purchased Electricity, Natural Gas, and Steam by Supplier Type,
  Manufacturing Industry, and Region
- Table 7.7 — Quantities of Purchased Electricity, Natural Gas, and Steam by Supplier Type,
  Manufacturing Industry, and Region
- Table 7.10 — Expenditures for Purchased Electricity, Natural Gas, and Steam by Supplier Type,
  Manufacturing Industry, and Region

Direct XLSX URLs:
- https://www.eia.gov/consumption/manufacturing/data/2022/xls/Table3_1.xlsx
- https://www.eia.gov/consumption/manufacturing/data/2022/xls/Table7_3.xlsx
- https://www.eia.gov/consumption/manufacturing/data/2022/xls/Table7_7.xlsx
- https://www.eia.gov/consumption/manufacturing/data/2022/xls/Table7_10.xlsx

## Important integration rule
MECS values are U.S. manufacturing survey estimates.

Their U.S. manufacturing-survey provenance remains explicit. They provide no
basis for fictional European beverage-site labels or direct joins to unrelated
real plant datasets.

Use this source for:
- manufacturing natural-gas benchmark ranges;
- purchased-steam benchmark ranges;
- purchased-energy price and expenditure benchmarks;
- industry-level fuel-mix comparisons;
- calibration of financial or energy models where explicitly documented.

The survey supports industry-level benchmarks; site and line meter readings,
utility bills, emissions, and product-level intensity require separate
operational evidence.

## Storage workflow
1. Preserve the official XLSX files unchanged in Bronze.
2. Validate file presence and workbook structure.
3. Preserve EIA suppression, estimation, footnote and unit conventions.
4. Convert source sheets conservatively to Parquet in Silver.
5. Map business fields only after inspecting the actual workbook structures.

No synthetic rows are included in this package.
