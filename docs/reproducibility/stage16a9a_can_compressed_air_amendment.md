# Stage 16A.9A can-line compressed-air amendment

## Accepted change

`CAN_ENERGY_250.compressed_air_nm3_per_1000_units` is now the synthetic
design assumption `5.0 Nm³/1,000 cans`. It is not measured Velora plant data.
The calculation uses the existing generic utility formula:

`compressed_air_nm3 = intensity × actual_quantity / 1,000`

for positive-production rows. PET assumptions remain 20.0, 22.0, and 30.0
Nm³/1,000 units. Production and idle electrical power assumptions and every
electricity formula are unchanged.

## Published external basis

The assumption is anchored to published manufacturer pneumatic-demand
specifications that establish that can filling/seaming equipment requires clean,
dry compressed air and that demand varies materially with machine scope and
configuration:

- Wild Goose Filling, WGC-50 specification: 1 cfm at 90 psi.
  <https://wildgoosefilling.com/wp-content/uploads/2019/10/WGC-50-Spec-Sheet_2019-Q4.pdf>
- Wild Goose Filling, Single Lane Evolution Series: 15–50 cans/minute and
  12.2 cfm at 90 psi.
  <https://wildgoosefilling.com/products/single-lane-evolution-series>
- Cask ACS V5: 40 cans/minute, 3 cfm at 90 psi for filler/seamer and 15 cfm
  for the total system including the standard air dryer.
  <https://www.cask.com/canning-systems/acs-automated-canning-system-v5/>

These external specifications are reference/basis information, not Velora
observations. Because equipment boundaries and line speeds differ, the project
does not linearly extrapolate any one machine specification. The fixed 5.0 value
is a conservative synthetic design selection for the fictional integrated line.

## Generator record

- Generator: `synthetic/generators/generate_energy_utilities.py`
- Version: `stage3h-energy-utilities-v2-can-air-5nm3-per-1000`
- Seed: `20260825`
- Generator SHA-256:
  `21fb23abdf15e770dacf3b40656864987b7ea655c40d77b485744b3dc607a181`

Relevant generator amendment:

```text
CAN_ENERGY_250.compressed_air_nm3_per_1000_units: NaN -> 5.0
summary: record generator version/seed and separate PET, can, and enterprise air totals
```

No electricity constant, electricity formula, weather rule, PET compressed-air
assumption, production dependency, or site aggregation was changed.

## Old-versus-new reconciliation

| Check | Result |
|---|---:|
| Affected can-line rows | 6,579 |
| Newly populated can-line rows | 6,579 |
| Positive-production can-line nulls after | 0 |
| Old can-line compressed air | 0.000 Nm³ |
| New can-line compressed air | 12,805,152.250 Nm³ |
| Old/new PET compressed air | 331,230,504.302 Nm³ / identical |
| Old enterprise compressed air | 331,230,504.302 Nm³ |
| New enterprise compressed air | 344,035,656.552 Nm³ |
| Increase attributable only to can lines | 12,805,152.250 Nm³ |

All 21 non-compressed-air line fields are row-level identical. Both PET
compressed-air fields are identical. Every field in the 13,158-row site output
is identical. This includes exact equality for line production electricity,
line idle electricity, line total electricity, line energy intensity, site
auxiliary electricity, site total electricity, and site energy intensity.

Machine-readable hashes and reconciliation evidence are in
`config/stage3h_energy_artifact_manifest.json`.

## Downstream boundary

Stage 12D reads line electricity, idle electricity, production, and weather
features. Stage 12E forecasts production and site total electricity. Neither
script selects compressed-air fields, so neither accepted model is retrained.

OEE, downtime, quality, maintenance, reliability, technical-opportunity, and
business-case artifacts are outside this generator's outputs and were not
regenerated.

## PostgreSQL and Power BI propagation

Stage 16A.10 completed authenticated propagation through the canonical runner
against the retained disposable database
`manufacturing_intelligence_stage16a10_20260828_proof1`. The existing
`manufacturing_intelligence` database was not targeted. The commands below show
the equivalent targeted validation shape for an authorized PostgreSQL session:

```powershell
python .\pipelines\postgres\load_energy_details.py `
  --host localhost --port 5433 `
  --dbname manufacturing_intelligence_stage16a10_20260828_proof1 --user postgres

& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
  -h localhost -p 5433 -U postgres -d manufacturing_intelligence_stage16a10_20260828_proof1 `
  -v ON_ERROR_STOP=1 -f .\sql\validation\200_validate_energy_views.sql

& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
  -h localhost -p 5433 -U postgres -d manufacturing_intelligence_stage16a10_20260828_proof1 `
  -v ON_ERROR_STOP=1 -f .\sql\validation\210_validate_utility_views.sql

& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
  -h localhost -p 5433 -U postgres -d manufacturing_intelligence_stage16a10_20260828_proof1 `
  -v ON_ERROR_STOP=1 -f .\sql\validation\410_validate_gold_models.sql

& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
  -h localhost -p 5433 -U postgres -d manufacturing_intelligence_stage16a10_20260828_proof1 `
  -v ON_ERROR_STOP=1 `
  -f .\sql\validation\415_validate_stage16a9a_can_air_powerbi.sql
```

The utility, Gold, and `gold_bi` objects are ordinary views over the refreshed
detail tables; their SQL definitions did not change. SQL 415 is the versioned,
fail-fast check of the fact, Gold, and Power BI-facing layers: 6,579 can-line
rows, zero compressed-air nulls, intensity 5.0, total 12,805,152.250 Nm3, and
the existing quantity-based utility formula. The PBIX does not require a model
change. SQL 415 passed with 6,579 CAN rows, zero positive-production CAN
compressed-air nulls, 5.0 Nm3/1,000 cans, and 12,805,152.250 Nm3 total. PBIX
refresh and visual confirmation remain manual for Stage 16B.
