# Industrial energy cost and improvement benchmark

## Domain
Industrial energy-cost, facility-profile, recommendation, savings, implementation, and payback benchmark data.

## Authoritative source
U.S. Department of Energy Industrial Training and Assessment Centers (ITAC) Database.

Official database page:
https://itac.university/download

Direct database archive:
https://itac.university/storage/ITAC_Database.zip

Open Energy Data Initiative mirror/catalog:
https://data.openei.org/submissions/281

## Source snapshot
The ITAC download page on 2026-08-24 reported:

- Format: zipped Excel workbook
- Generated: 2026-08-24
- Size: approximately 15.58 MB
- Assessments: 23,121
- Recommendations: 169,956

The database contains real industrial/manufacturing assessment information including facility profile,
industry, size, products, energy use/cost context, and energy-efficiency recommendations with estimated
energy and dollar savings, project cost, implementation status, and payback-related information.

## Important integration rule
These records belong to real U.S. industrial facilities assessed by the ITAC/IAC program.

They MUST NOT be relabelled as records from the fictional European beverage manufacturer and MUST NOT
be row-level joined to the bottling-line, MetroPT, SECOM, hydraulic-system, or other unrelated datasets.

Use this source for:
- industrial energy-cost benchmarking;
- empirical distributions of recommendation cost and savings;
- payback and implementation analysis;
- calibration of financial opportunity models;
- examples of energy-efficiency opportunity categories;
- plant-level energy intensity studies where source fields support them.

Do not use it to invent:
- beverage-plant utility bills;
- line-level energy tariffs;
- steam/compressed-air meter readings;
- site-specific production losses.

## Storage workflow
1. `bronze/itac/` — preserve the downloaded ZIP/XLSX unchanged.
2. `silver/itac/` — normalize workbook sheets and write columnar Parquet files.
3. Gold benchmark models may aggregate by industry, recommendation category, energy type, savings,
   project cost, payback, and implementation status while retaining source provenance.

No synthetic rows are included in this package.
