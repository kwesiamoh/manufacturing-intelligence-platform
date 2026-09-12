# Canonical clean-build order

Status: accepted v1.0.0 build definition with retained disposable clean-build proof
Manifest: [`config/artifact_manifest.json`](../../config/artifact_manifest.json)  
Production seed manifest:
[`config/canonical_production_seed.json`](../../config/canonical_production_seed.json)  
Clean-build proof:
[`clean_build_proof.md`](clean_build_proof.md)
Scope: canonical Velora operational PostgreSQL/Power BI build, including the
governed enterprise telemetry adaptation, with real-source model and external
benchmark reproduction documented separately; no AWS deployment

## What this document does

This document defines the accepted execution order for the Velora operational
database and BI state. The governed MetroPT-informed enterprise telemetry is a
canonical materialized input. Full real-source MetroPT model reproduction and
the hydraulic portfolio benchmark are defined separately.
The retained proof records execution of this order through the canonical runner
against a disposable database.

`pipelines/postgres/bootstrap_database.ps1` is the supported clean-database
build entry point.

## Reproducibility boundary and provenance

The canonical upstream boundary is the governed, materialized Silver production
artifact:

`data/silver/synthetic_enterprise/production/production_operations_2024_2025.parquet`

This artifact supplies the central 65,790-row production population used by
downstream synthetic generators and the PostgreSQL fact loader. The repository
cannot regenerate that population from first principles because the production
generator is unavailable. Exact reconstruction from the retained evidence would
require inventing parameters and random-generation behavior. The immutable
governed seed is enforced by `config/canonical_production_seed.json` and
`scripts/verify_canonical_production_seed.py`.

### Production boundary evidence

The project-local search covered Python code, documentation, JSON manifests,
generation configuration, SQL/schema and validation files, data dictionaries,
logs, source inventories, downstream generators, and the retained Bronze and
Silver production artifacts. No production-generation implementation, notebook,
project-local archive, backup, or command transcript containing that
implementation is retained.

The evidence separates as follows:

- Directly evidenced: seed `20260825`; six sites; 30 lines; three daily shifts;
  2024-01-01 through 2025-12-31 production starts; one row per
  line/shift/timestamp business grain; synthetic provenance; quantity
  reconciliation; and high-level shift, break, campaign, and changeover
  configuration.
- Serialization evidence: the governed manifest records that the retained local
  Bronze CSV contains the same 65,790 logical table values as the canonical
  Silver Parquet. The public release excludes the Bronze serialization.
- Unavailable from retained evidence: exact per-row campaign/product assignment,
  probability distributions, random draw order, site/line effects, and the
  complete formulas/parameterization that produced every accepted business
  value.

The canonical artifact controls are:

| Control | Expected value |
|---|---|
| Path | `data/silver/synthetic_enterprise/production/production_operations_2024_2025.parquet` |
| Physical SHA-256 | `57772350e5a75c7245958af6ec54d2b19e1d863e58adf7280f7f1114db7dd1b7` |
| Logical content fingerprint | `bb7a789c9231224f1d72b013081d806fb721bab43a8ebd8fdb7e5898889c66f3` |
| Schema version | `velora-production-silver-v1` |
| Row count | 65,790 |
| Primary key | `production_record_id` (unique) |
| Business grain | `timestamp_start`, `site_code`, `line_code`, `shift_code` (unique) |
| Coverage | 731 start dates, 6 sites, 30 lines, 6 products, 3 shifts |

The manifest contains the exact 27-column schema and data types, date limits,
coverage members, zero-null profile, ordering assumptions, provenance
constants, and reconciliation totals. The logical fingerprint sorts by the
unique production record ID and canonicalizes typed values, so it is independent
of row order and Parquet writer metadata.

The six-site Velora enterprise data is fictional synthetic integration data.
Original MetroPT and hydraulic condition-monitoring records are real external
data and are never Velora operational observations. The MetroPT-informed
enterprise compressor scenario is explicitly synthetic. Eurostat and
weather records retain real external benchmark/context provenance even where
they are combined with synthetic enterprise records.

## Invocation conventions

All paths below are repository-relative. Run from the repository root.
Use one consistent PostgreSQL endpoint throughout; the current downstream code
defaults to `localhost:5433`, database `manufacturing_intelligence`, user
`postgres`. Override the database parameter for disposable validation builds.

The canonical implementation entry point is:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File .\pipelines\postgres\bootstrap_database.ps1 `
  -PgHost localhost -PgPort 5433 `
  -PgDatabase manufacturing_intelligence -PgUser postgres
```

Those parameters are passed to every required loader and DQ/BI bridge script.
The default port is 5433. Use `-SkipDatabaseCreation` only when the configured
database already exists and the executing user cannot create databases.

For each SQL file, the canonical direct invocation shape is:

```powershell
& psql -h localhost -p 5433 -U postgres `
  -d manufacturing_intelligence -v ON_ERROR_STOP=1 `
  -f .\path\to\file.sql
```

SQL `000_create_database.sql` is the exception: connect it to the administrative
`postgres` database. All mandatory SQL validators contain enforcing gates and
run with `ON_ERROR_STOP=1`; a failed mandatory check therefore prevents the
runner from reporting completion. Legitimate DQ `WARN` results remain nonfatal.

Python loaders accept the database flags shown below:

```powershell
python .\path\to\loader.py `
  --host localhost --port 5433 `
  --dbname manufacturing_intelligence --user postgres
```

The loaders use standard external libpq credentials (including pgpass) when
available and otherwise prompt interactively. Repository files and evidence
contain no credentials.

## Phase 0 - required materialized inputs

Before creating the database, verify the governed production boundary first:

```powershell
python .\scripts\verify_canonical_production_seed.py `
  --manifest .\config\canonical_production_seed.json
```

This read-only gate returns nonzero if the manifest or artifact is missing, or
if the artifact's physical hash, logical content, schema, row count, key/grain,
coverage, null profile, provenance constants, or reconciliation values differ.
The canonical bootstrap runs this gate during preflight before any database
creation or mutation.

Then verify that the remaining materialized inputs exist and preserve their
recorded provenance.

- Synthetic master/configuration CSVs under `data_model/` and
  `synthetic/config/`.
- The governed/materialized synthetic production Silver input:
  `data/silver/synthetic_enterprise/production/production_operations_2024_2025.parquet`.
- Real external weather context:
  `sources/era5-weather/data/silver/weather/enterprise_weather_context_2024_2025.parquet`.
- Real external reference/benchmark Silver data used by
  `pipelines/postgres/load_reference_datasets.py` from the FMU maintenance,
  industrial energy assessment, industrial water, manufacturing fuels, EU ETS,
  and Eurostat packages.
- Structured Eurostat input:
  `sources/eurostat-energy-prices/silver/eurostat_energy_prices/nrg_pc_205__six_site_countries_2024_2025.parquet`.

The canonical clean-database sequence begins from materialized inputs;
acquisition workflows handle downloads separately. If the
structured Eurostat Parquet is absent but its materialized source is present,
the accepted transformation is
`pipelines/silver/expand_eurostat_nrg_pc_205.py`. The downloader
`pipelines/bronze/download_eurostat_nrg_pc_205.py` belongs to source acquisition
and is never invoked by the database build.

### Downstream synthetic regeneration from governed Silver production

This path can rebuild the downstream synthetic artifacts without rewriting the
governed Silver production input. Its exact dependency order is:

1. `synthetic/generators/generate_downtime_events.py`
2. `synthetic/generators/generate_quality_events.py`
3. `synthetic/generators/generate_maintenance_work_orders.py`
4. `synthetic/generators/generate_energy_utilities.py`

The downtime and quality generators independently consume the governed
production Silver artifact. Maintenance generation requires the downtime
output. Energy generation requires the governed production Silver artifact plus
the real external weather-context Parquet. These steps regenerate downstream
facts from the governed boundary; first-principles production regeneration is
unavailable. The same verified production columns
also satisfy `pipelines/postgres/load_synthetic_facts.py`.

## Phase 1 - database and schema

Execute these files in exactly this order:

1. Connect to `postgres` and execute
   `sql/admin/000_create_database.sql`.
2. Connect to `manufacturing_intelligence` and execute
   `sql/ddl/001_create_dimensions.sql`.
3. Execute `sql/ddl/002_create_facts.sql`.
4. Execute `sql/migrations/004_add_fact_lineage.sql`.
5. Execute `sql/migrations/005_add_maintenance_downtime_source_lineage.sql`.
6. Execute `sql/migrations/006_create_metropt_predictive_maintenance.sql`.
7. Execute `sql/ddl/003_seed_static_dimensions.sql`.
8. Execute `sql/ddl/004_create_reference_tables.sql`.
9. Execute `sql/ddl/005_create_loss_value_config.sql`.
10. Execute `sql/ddl/006_create_energy_detail_tables.sql`.
11. Execute `sql/ddl/007_create_eurostat_price_observations.sql`.
12. Execute `sql/ddl/008_create_data_quality_tables.sql`.
13. Execute `sql/ddl/009_seed_data_quality_rules.sql`.

Migration 005 adds the referenced downtime source to each maintenance lineage
link. Existing Velora rows are backfilled only when the downtime event exists
under the maintenance row's established `SYNTHETIC_ENTERPRISE` source. The
source-qualified relationship avoids any assumption that textual event IDs are
globally unique and permits multiple work orders for one downtime event.

## Phase 2 - dimensions, facts, references, and supplemental data

Execute these loaders in exactly this order:

14. `pipelines/postgres/load_master_dimensions.py`
15. `pipelines/postgres/load_synthetic_facts.py`
16. `pipelines/postgres/load_reference_datasets.py`
17. `pipelines/postgres/load_energy_details.py`
18. `pipelines/postgres/load_eurostat_electricity_prices.py`
19. `pipelines/postgres/load_metropt_predictive_maintenance.py`

The supplemental loaders at positions 17 through 19 are mandatory. The reference
loader retains real external records exclusively in `ref_*` tables, outside the
synthetic Velora facts. The telemetry loader consumes the governed 42,598-row
materialized enterprise adaptation and preserves the real MetroPT source and
synthetic scenario identifiers separately.

After the Eurostat price loader, run the enforcing Python database validation:

20. `pipelines/postgres/validate_database.py`

The validator enforces stable governed populations and requires the recursively
loaded generic Eurostat reference table to be non-empty.

## Phase 3 - core production, energy, utilities, and cost analytics

Execute these SQL files in exactly this order:

21. `sql/analytics/100_create_oee_views.sql`
22. `sql/analytics/110_create_production_loss_views.sql`
23. `sql/analytics/120_create_production_benchmark_views.sql`
24. `sql/analytics/200_create_energy_views.sql`
25. `sql/analytics/210_create_utility_views.sql`
26. `sql/analytics/220_create_energy_cost_views.sql`

SQL 220 is a mixed-provenance benchmark: synthetic enterprise consumption
multiplied by real external Eurostat price observations. The resulting cost is a
modeled benchmark and has no measured Velora tariff provenance.

## Phase 4 - DQ execution and reporting views

Execute in this order:

27. `pipelines/postgres/run_data_quality.py`
28. `sql/analytics/300_create_data_quality_views.sql`

The runner returns nonzero for mandatory failures while preserving legitimate
`WARN` results as nonfatal. The 29-rule enterprise population includes five
telemetry rules. Its cadence rule quantifies retained source gaps without
classifying physical faults or analytical warning states as data defects.

## Phase 5 - Gold and Power BI compatibility layer

Execute in this order:

29. `sql/analytics/400_create_gold_models.sql`
30. `sql/analytics/410_create_powerbi_compat_views.sql`

SQL 400 depends on the production, energy, and utilities analytical views and
the SQL 300 DQ views. SQL 410 must exist before the energy anomaly and
forecasting workflows because those Python scripts query `gold_bi`.

## Phase 6 - accepted SQL analytical layers

Execute in this order:

31. `sql/analytics/622_create_quality_reject_laney_pprime.sql`
32. `sql/analytics/720_create_reliability_kpis.sql`
33. `sql/analytics/730_create_failure_downtime_analysis.sql`
34. `sql/analytics/742_create_reliability_trends.sql`
35. `sql/analytics/760_create_metropt_predictive_maintenance_views.sql`

SQL 622 is self-contained apart from
`gold_bi.vw_shift_manufacturing_performance`; the ordinary p-chart diagnostic
has no executable dependency role. SQL 742 is the retained creator for the monthly
reliability view names.

SQL 720 defines the canonical reliability relationship at two explicit grains:
one row per source-qualified maintenance/work-order link and one row per linked
downtime failure event. SQL 730 and SQL 742 consume the failure-event grain, so
multiple legitimate work orders can contribute repair duration without
multiplying failure counts or downtime. SQL 742 uses linked production-date
attribution and source-qualifies that production join.

## Phase 7 - accepted advanced analytics and BI landing tables

The database must first contain the Gold BI views from position 28. The
canonical database build treats the accepted energy-anomaly and forecasting
Parquets as governed materialized inputs. The bootstrap preflight requires both files and
fails before database mutation if either is absent. Model training is a
separate, optional workflow.

Then execute:

36. `scripts/load_powerbi_advanced_analytics.py`
37. `sql/analytics/750_create_powerbi_advanced_analytics_views.sql`

The advanced-analytics loader receives the same host, port, database, and user parameters as the other
canonical loaders. It consumes only these accepted materialized outputs:

- `data/gold/advanced_analytics/energy_anomaly/energy_anomaly_shift_monitoring_2025.parquet`
- `data/gold/advanced_analytics/forecasting/daily_site_forecast_holdout_2025.parquet`

The loader validates and hashes these inputs before database mutation. It keeps
stable landing-table objects and performs the replacement as a single
transactional `TRUNCATE + COPY` operation, preserving dependent `gold_bi` views
across reruns. It also validates the reliability source, records a
successful-load audit row, and rolls back to the prior landing contents if any
acceptance condition fails. Reliability downtime uses the accepted `14,856.65`
hour snapshot with a `+/- 0.01` hour tolerance. `--forecast-path` and
`--anomaly-path` provide
explicit input overrides; `--validate-only` performs input validation and
checksum calculation without contacting PostgreSQL.

SQL 750 also consumes the reliability views from SQL 742. Run the
loader before SQL 750 on a fresh database. On an existing database, the loader's
transactional refresh preserves the stable landing tables, so SQL 750's
dependent `gold_bi` views remain available during a rerun.

The governed telemetry load and its predictive-maintenance Gold views are
already present at this point. This run neither rebuilds the real-source MetroPT
model nor the hydraulic benchmark.

## Phase 8 - final mandatory validations

Execute every validation below after position 37, in this exact order. Use
`ON_ERROR_STOP=1` for each psql call.

38. `sql/admin/010_verify_schema.sql`
39. `sql/validation/020_dimension_counts.sql`
40. `sql/validation/030_synthetic_fact_counts.sql`
41. `sql/validation/040_reference_counts.sql`
42. `sql/validation/050_database_validation.sql`
43. `sql/validation/100_validate_oee_views.sql`
44. `sql/validation/110_validate_production_loss.sql`
45. `sql/validation/120_validate_production_benchmark.sql`
46. `sql/validation/200_validate_energy_views.sql`
47. `sql/validation/210_validate_utility_views.sql`
48. `sql/validation/220_validate_energy_cost.sql`
49. `sql/validation/300_validate_data_quality.sql`
50. `sql/validation/410_validate_gold_models.sql`
51. `sql/validation/623_validate_quality_reject_laney_pprime.sql`
52. `sql/validation/721_validate_reliability_kpis.sql`
53. `sql/validation/731_validate_failure_downtime_analysis.sql`
54. `sql/validation/743_validate_reliability_trends.sql`
55. `sql/validation/761_validate_metropt_predictive_maintenance.sql`
56. `sql/validation/415_validate_can_air_powerbi.sql`
57. `sql/validation/751_validate_powerbi_advanced_analytics_views.sql`

The canonical runner executes all 20 files as mandatory fail-fast gates. The
retained disposable proof records the 19-gate platform boundary captured before
the governed telemetry integration; the current runner adds SQL 761. SQL 623 materializes the
unchanged accepted Laney p-prime view once in a session-local temporary table
for validation because repeatedly expanding that nested view is computationally
expensive. This affects validation execution only; the accepted SPC formulas
and view definition remain intact.

## Phase 9 - Power BI manual refresh and verification

After all database validations have been reviewed:

58. Open `powerbi/Velora_Manufacturing_Intelligence.pbix` in Power BI Desktop.
59. Refresh against the selected local database.
60. Verify relationships, measures, page filters, accepted advanced-analytics
    visuals, and provenance labels.

The PBIX is a binary manual artifact that the canonical build leaves untouched.

## Supporting business-case evidence

Business-case evidence is reproducible after the governed production input and
accepted loss-accounting definition are present. The Velora PostgreSQL/Power BI
operational clean build neither consumes nor requires this supporting evidence.

Generate and immediately validate the versioned evidence:

```powershell
python -B .\scripts\generate_business_case_opportunity_evidence.py
```

Validate the retained exports without rewriting them:

```powershell
python -B .\scripts\generate_business_case_opportunity_evidence.py --validate-only
```

The generator reproduces
`public.vw_site_loss_summary.total_technical_opportunity_eur` from the governed
production seed and SQL 005 product-value configuration, using the calculation
defined by SQL 100 and SQL 110. It emits six site rows, annual sensitivity
scenarios, and a JSON provenance/checksum manifest under
`data/gold/business_case/`. The validator fails on schema/grain/period/value,
reconciliation, canonical-input, or retained-output checksum discrepancies.
The exported EUR 573,908,429.76 is a synthetic modeled technical opportunity
for the two-year 2024-2025 period. Realized savings require operational
evidence. EUR 286,954,214.88/year is the simple annualized base; this arithmetic
calculation is not a forecast.

## Public-source orchestration

The 14 real external source packages have a separate, explicit runner and
manifest:

- `sources/run_all_sources.ps1`
- `sources/source_pipeline_manifest.json`
- `requirements.txt`

The source runner operates independently of the Velora clean-database sequence.
It resolves from its own repository location and can be called from any working
directory. Use `-DryRun` to inspect all action paths and states without
executing downloads, validators, or transformations.

Acquisition modes, credentials, redistribution boundaries, and package-specific
commands are maintained in the [source orchestration guide](../../sources/README.md)
and [third-party data policy](../governance/third_party_data_redistribution.md).

## Optional source-model and benchmark reproduction

The following model-reproduction paths are optional workflows independent of
the canonical clean build.
The materialized enterprise telemetry is already a governed build input; these
steps regenerate it from acquired real-source data. Neither optional workflow
is required by the retained Power BI report.

### MetroPT source-model regeneration

To reproduce the source-qualified anomaly score, selected policy, real
early-warning evaluation, and governed enterprise adaptation:

1. Run `scripts/run_metropt_anomaly_scoring.py` to recreate the fixed anomaly
   score/model and `metropt_anomaly_windows.parquet` support artifact.
2. Run `scripts/select_metropt_alert_policy.py` to recreate the
   accepted selected-policy outputs.
3. Run `scripts/run_metropt_predictive_maintenance.py` to evaluate the 2-, 4-,
   and 6-hour real warning horizons and create the explicitly synthetic
   MetroPT-informed enterprise compressor scenario.
4. Validate the regenerated materialized inputs with
   `pipelines/postgres/load_metropt_predictive_maintenance.py --validate-only`.

The anomaly-scoring workflow supplies the score artifact required downstream.
The real MetroPT evaluation and controlled synthetic enterprise result retain
separate scenario scopes and provenance fields.

### Optional hydraulic analytical benchmark

The real external input boundary is
`sources/hydraulic-condition-monitoring/silver/reliability/`. Reproduce the accepted result
as follows:

1. If `data/gold/advanced_analytics/hydraulic_condition/hydraulic_cycle_features.parquet`
   is absent, run
   `scripts/prepare_hydraulic_features.py` once to build
   that support artifact. The published result is limited to the accepted
   classification workflow; the embedded baseline model remains supporting
   material only.
2. Run `scripts/run_hydraulic_condition_classification.py` for the
   accepted benchmark outputs.

The hydraulic feature cache, models, and outputs remain external to the Velora
operational PostgreSQL and Power BI layers.

## Related documentation

- [Artifact classifications](../../config/artifact_manifest.json)
- [Analytics methodology and limitations](../methodology/analytics_methodology_and_limitations.md)
- [Clean-build proof](clean_build_proof.md)
- [Source orchestration](../../sources/README.md)
