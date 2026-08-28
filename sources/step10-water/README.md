# Step 10 — Real Manufacturing Water Intake Benchmark

## Domain
Manufacturing water intake by industrial sector and purpose of initial use.

## Authoritative source
Statistics Canada — Industrial Water Survey

Table:
**38-10-0056-01 — Water intake in manufacturing industries, by purpose of initial use and by industry**

Official table:
https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3810005601

Official catalogue:
https://www150.statcan.gc.ca/n1/en/catalogue/3810005601

Official full-table CSV:
https://www150.statcan.gc.ca/n1/tbl/csv/38100056-eng.zip

DOI:
https://doi.org/10.25318/3810005601-eng

## Source characteristics
- Geography: Canada
- Source program: Industrial Water Survey
- Industrial detail: 3-digit NAICS manufacturing industries
- Frequency: Occasional
- Latest published table release: 2024-03-18
- Published reference periods include 2013, 2015, 2017, 2020 and 2021
- Unit: millions of cubic metres
- Purposes include:
  - process water;
  - cooling, condensing and steam;
  - sanitary/domestic use;
  - other initial uses.

Statistics Canada also publishes data-quality symbols based on coefficient-of-variation ranges.
Those source flags must be preserved.

## Important integration rule
These are Canadian manufacturing-industry survey estimates, not measurements from the fictional
European beverage sites.

Use this dataset for:
- industrial water-use benchmarking;
- comparison across manufacturing industries;
- process-water versus cooling/condensing/steam demand;
- empirical calibration of later site-level water assumptions if such synthetic integration is explicitly documented.

Do not:
- relabel Canadian survey values as beverage-plant meter readings;
- invent line-level water consumption;
- infer daily/hourly water telemetry from annual survey totals;
- remove Statistics Canada data-quality flags.

## Storage workflow
1. Keep the downloaded ZIP/CSV unchanged in Bronze.
2. Validate table identifier and expected source fields.
3. Normalize column names only.
4. Preserve flags, units, scalar factors and status fields.
5. Write the cleaned table to Parquet in Silver.

No synthetic records are included.
