# Canonical clean-build order

Status: Stage 16A.1 canonical definition; implemented and hardened through
Stage 16A.10, with a retained disposable clean-build proof  
Manifest: [`config/artifact_manifest.json`](../../config/artifact_manifest.json)  
Production seed manifest:
[`config/canonical_production_seed.json`](../../config/canonical_production_seed.json)  
Stage 16A.10 proof:
[`stage16a10_clean_build_proof.md`](stage16a10_clean_build_proof.md)  
Scope: canonical Velora operational PostgreSQL/Power BI build, with external
benchmark reproduction documented separately; no AWS deployment

## What this document does

This document defines the accepted execution order for the Velora operational
database and BI state. Optional MetroPT and hydraulic portfolio benchmarks are
defined in separate sections and are not inputs to that operational build.
Stage 16A.10 executed this order through the canonical runner against a new
disposable database and captured the resulting proof separately.

`pipelines/postgres/bootstrap_database.ps1` is the canonical Stage 16A.2 build
entry point. The older Stage 4 and Stage 9 runners remain partial convenience
artifacts and are not clean-build entry points.

## Reproducibility boundary and provenance

The canonical upstream boundary is the governed, materialized Silver production
artifact:

`data/silver/synthetic_enterprise/production/production_operations_2024_2025.parquet`

This artifact supplies the central 65,790-row production population used by
downstream synthetic generators and the PostgreSQL fact loader. The repository
cannot regenerate that population from first principles. Stage 16A.5 did not
recover the original generator, and exact reconstruction from the current
repository evidence would require inventing parameters and random-generation
behavior. The accepted outcome is therefore an immutable governed canonical
seed, enforced by `config/canonical_production_seed.json` and
`scripts/verify_canonical_production_seed.py`.

`synthetic/generators/bronze_to_silver_production.py` is only a converter and
validator for a retained Bronze CSV. It is not the missing production generator,
does not resolve the origin gap, and is not part of the canonical upstream
regeneration path defined here.

### Stage 16A.5 evidence and decision

The project-local search covered Python code, documentation, JSON manifests,
generation configuration, SQL/schema and validation files, data dictionaries,
logs, source inventories, downstream generators, and the retained Bronze and
Silver production artifacts. No production-generation implementation,
notebook, project-local archive/backup, or command transcript containing the
missing implementation was found. No Git recovery is claimed because usable Git
history is not present in this workspace snapshot.

The evidence separates as follows:

- Directly evidenced: seed `20260825`; six sites; 30 lines; three daily shifts;
  2024-01-01 through 2025-12-31 production starts; one row per
  line/shift/timestamp business grain; synthetic provenance; quantity
  reconciliation; and high-level shift, break, campaign, and changeover
  configuration.
- Recoverable deterministic transformation: the retained Bronze CSV parses to
  the same 65,790 logical table values as the canonical Silver Parquet, and
  `bronze_to_silver_production.py` validates and serializes that table.
- Not recoverable without guessing: exact per-row campaign/product assignment,
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
MetroPT and the hydraulic condition-monitoring dataset are real external
benchmark demonstrations and are never Velora operational data. Eurostat and
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
available and otherwise prompt interactively. Credentials are not stored in
repository files or evidence.

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

Then verify that the remaining materialized inputs exist. Do not relabel their
provenance.

- Synthetic master/configuration CSVs under `data_model/` and
  `synthetic/config/`.
- The governed/materialized synthetic production Silver input:
  `data/silver/synthetic_enterprise/production/production_operations_2024_2025.parquet`.
- Real external weather context:
  `sources/step13-weather/data/silver/weather/enterprise_weather_context_2024_2025.parquet`.
- Real external reference/benchmark Silver data used by
  `pipelines/postgres/load_reference_datasets.py` under source Steps 6, 8, 10,
  11, 12, and 14.
- Structured Eurostat input:
  `sources/step14-eu-energy-prices/silver/eurostat_energy_prices/nrg_pc_205__six_site_countries_2024_2025.parquet`.

Downloads are not part of the canonical clean-database sequence. If the
structured Eurostat Parquet is absent but its materialized source is present,
the accepted transformation is
`pipelines/silver/expand_eurostat_nrg_pc_205.py`. The downloader
`pipelines/bronze/download_eurostat_nrg_pc_205.py` is an acquisition step, not a
database-build step.

### Downstream synthetic regeneration from governed Silver production

This path can rebuild the downstream synthetic artifacts without rewriting the
governed Silver production input. Its exact dependency order is:

1. `synthetic/generators/generate_downtime_events.py`
2. `synthetic/generators/generate_quality_events.py`
3. `synthetic/generators/generate_maintenance_work_orders.py`
4. `synthetic/generators/generate_energy_utilities.py`

Steps 1 and 2 independently consume the governed production Silver artifact.
Step 3 requires Step 1. Step 4 requires the governed production Silver artifact
plus the real external weather-context Parquet. This is downstream regeneration,
not first-principles production regeneration. The same verified production
columns also satisfy `pipelines/postgres/load_synthetic_facts.py`.

## Phase 1 - database and schema

Execute these files in exactly this order:

1. Connect to `postgres` and execute
   `sql/admin/000_create_database.sql`.
2. Connect to `manufacturing_intelligence` and execute
   `sql/ddl/001_create_dimensions.sql`.
3. Execute `sql/ddl/002_create_facts.sql`.
4. Execute `sql/migrations/004_add_fact_lineage.sql`.
5. Execute `sql/migrations/005_add_maintenance_downtime_source_lineage.sql`.
6. Execute `sql/ddl/003_seed_static_dimensions.sql`.
7. Execute `sql/ddl/004_create_reference_tables.sql`.
8. Execute `sql/ddl/005_create_loss_value_config.sql`.
9. Execute `sql/ddl/006_create_energy_detail_tables.sql`.
10. Execute `sql/ddl/007_create_eurostat_price_observations.sql`.
11. Execute `sql/ddl/008_create_data_quality_tables.sql`.
12. Execute `sql/ddl/009_seed_data_quality_rules.sql`.

Migration 005 adds the referenced downtime source to each maintenance lineage
link. Existing Velora rows are backfilled only when the downtime event exists
under the maintenance row's established `SYNTHETIC_ENTERPRISE` source. It does
not assume textual event IDs are globally unique and does not require one work
order per downtime event.

SQL DDL 010-012 are MetroPT benchmark DQ extensions and are not part of this
Velora operational path. Their optional order is documented later.

## Phase 2 - dimensions, facts, references, and supplemental data

Execute these loaders in exactly this order:

13. `pipelines/postgres/load_master_dimensions.py`
14. `pipelines/postgres/load_synthetic_facts.py`
15. `pipelines/postgres/load_reference_datasets.py`
16. `pipelines/postgres/load_energy_details.py`
17. `pipelines/postgres/load_eurostat_electricity_prices.py`

The two supplemental loaders in Steps 16 and 17 are mandatory. The existing
Stage 4 and Stage 9 runners currently omit them. The reference loader retains
real external records in `ref_*` tables; it does not load them as synthetic
Velora facts.

After Step 17, run the enforcing Python Stage 4 validation:

18. `pipelines/postgres/validate_stage4_database.py`

Known issue: its expected row count for `ref_eurostat_energy_price` is stale
relative to the current recursive reference loader. Preserve the check in this
definition, but do not claim a clean-build pass until the expectation is
reconciled in a later hardening step.

## Phase 3 - core production, energy, utilities, and cost analytics

Execute these SQL files in exactly this order:

19. `sql/analytics/100_create_oee_views.sql`
20. `sql/analytics/110_create_production_loss_views.sql`
21. `sql/analytics/120_create_production_benchmark_views.sql`
22. `sql/analytics/200_create_energy_views.sql`
23. `sql/analytics/210_create_utility_views.sql`
24. `sql/analytics/220_create_energy_cost_views.sql`

SQL 220 is a mixed-provenance benchmark: synthetic enterprise consumption
multiplied by real external Eurostat price observations. It is not a measured
Velora electricity tariff.

## Phase 4 - DQ execution and reporting views

Execute in this order:

25. `pipelines/postgres/run_stage7a_data_quality.py`
26. `sql/analytics/300_create_data_quality_views.sql`

The Stage 7A runner currently reports some failure states without necessarily
returning a failing process exit code. That behavior is recorded, not repaired,
by Stage 16A.1. Stage 7B MetroPT DQ is an optional external benchmark extension,
not a Velora operational input.

## Phase 5 - Gold and Power BI compatibility layer

Execute in this order:

27. `sql/analytics/400_create_gold_models.sql`
28. `sql/analytics/410_create_powerbi_compat_views.sql`

SQL 400 depends on the Stage 5 and 6 analytical views and SQL 300 DQ views. SQL
410 must exist before the accepted Stage 12D and 12E workflows, because those
Python scripts query `gold_bi`.

## Phase 6 - accepted SQL analytical layers

Execute in this order:

29. `sql/analytics/622_create_quality_reject_laney_pprime.sql`
30. `sql/analytics/720_create_stage13b_reliability_kpis.sql`
31. `sql/analytics/730_create_stage13c_failure_downtime_analysis.sql`
32. `sql/analytics/742_create_stage13d2_corrected_reliability_trends.sql`

SQL 622 is self-contained apart from
`gold_bi.vw_shift_manufacturing_performance`. It does not reference the view
created by SQL 620. Therefore SQL 620 is an optional superseded diagnostic, not
an executable dependency of the accepted Laney p-prime result.

Never run `sql/analytics/740_create_stage13d_reliability_trends.sql` in the
canonical build. SQL 740 and SQL 742 create the same monthly reliability view
names; SQL 740 contains the superseded attribution, while SQL 742 is accepted.

`sql/analytics/630_create_metropt_alert_landing_table.sql` is optional and is
not part of this build. The selected MetroPT policy remains a separate external
benchmark and is not integrated into Velora Power BI.

SQL 720 defines the canonical reliability relationship at two explicit grains:
one row per source-qualified maintenance/work-order link and one row per linked
downtime failure event. SQL 730 and SQL 742 consume the failure-event grain, so
multiple legitimate work orders can contribute repair duration without
multiplying failure counts or downtime. SQL 742 retains the corrected linked
production-date attribution and also source-qualifies that production join.

## Phase 7 - accepted advanced analytics and BI landing tables

The database must first contain the Gold BI views from Step 28. The canonical
database build treats the already-accepted Stage 12D and Stage 12E Parquets as
governed materialized inputs. The bootstrap preflight requires both files and
fails before database mutation if either is absent; it does not retrain models.

Then execute:

33. `scripts/load_powerbi_advanced_analytics.py`
34. `sql/analytics/750_create_powerbi_advanced_analytics_views.sql`

Step 33 receives the same host, port, database, and user parameters as the other
canonical loaders. It consumes only these accepted materialized outputs:

- `data/gold/advanced_analytics/energy_anomaly/energy_anomaly_shift_monitoring_2025.parquet`
- `data/gold/advanced_analytics/forecasting/daily_site_forecast_holdout_2025.parquet`

The loader validates and hashes these inputs before database mutation. It keeps
stable landing-table objects and performs the replacement as a single
transactional `TRUNCATE + COPY` operation, so reruns do not drop the dependent
`gold_bi` views. It also validates the corrected reliability source, records a
successful-load audit row, and rolls back to the prior landing contents if any
acceptance condition fails. Reliability downtime uses the accepted `14,856.65`
hour snapshot with a `+/- 0.01` hour tolerance. `--forecast-path` and
`--anomaly-path` provide
explicit input overrides; `--validate-only` performs input validation and
checksum calculation without contacting PostgreSQL.

SQL 750 also consumes the corrected reliability views from SQL 742. Run the
loader before SQL 750 on a fresh database. On an existing database, the loader's
transactional refresh preserves the stable landing tables, so SQL 750's
dependent `gold_bi` views do not block a rerun.

The Stage 12C MetroPT and Stage 13E.3 hydraulic workflows are accepted portfolio
benchmark demonstrations, but neither is executed in this Velora database/BI
phase and neither is loaded into Velora operational views.

## Phase 8 - final mandatory validations

Execute every validation below after Step 34, in this exact order. Use
`ON_ERROR_STOP=1` for each psql call.

35. `sql/admin/010_verify_schema.sql`
36. `sql/validation/020_dimension_counts.sql`
37. `sql/validation/030_synthetic_fact_counts.sql`
38. `sql/validation/040_reference_counts.sql`
39. `sql/validation/050_stage4g_database_validation.sql`
40. `sql/validation/100_validate_oee_views.sql`
41. `sql/validation/110_validate_production_loss.sql`
42. `sql/validation/120_validate_production_benchmark.sql`
43. `sql/validation/200_validate_energy_views.sql`
44. `sql/validation/210_validate_utility_views.sql`
45. `sql/validation/220_validate_energy_cost.sql`
46. `sql/validation/300_validate_data_quality.sql`
47. `sql/validation/410_validate_gold_models.sql`
48. `sql/validation/623_validate_quality_reject_laney_pprime.sql`
49. `sql/validation/721_validate_stage13b_reliability_kpis.sql`
50. `sql/validation/731_validate_stage13c_failure_downtime_analysis.sql`
51. `sql/validation/743_validate_stage13d2_corrected_reliability_trends.sql`
52. `sql/validation/415_validate_stage16a9a_can_air_powerbi.sql`
53. `sql/validation/751_validate_powerbi_advanced_analytics_views.sql`

SQL 621 is excluded because it validates optional superseded SQL 620. SQL 741
is excluded because it validates superseded SQL 740.

The canonical runner executes all 19 files as mandatory fail-fast gates. Stage
16A.10 proved the full set in a disposable database. SQL 623 materializes the
unchanged accepted Laney p-prime view once in a session-local temporary table
for validation because repeatedly expanding that nested view is computationally
expensive. This changes validation execution only, not accepted SPC formulas or
the view definition.

## Phase 9 - Power BI manual refresh and verification

After all database validations have been reviewed:

54. Open `powerbi/Velora_Manufacturing_Intelligence.pbix` in Power BI Desktop.
55. Refresh against the selected local database.
56. Verify relationships, measures, page filters, accepted advanced-analytics
    visuals, and provenance labels.

The PBIX is a binary manual artifact and is not modified by the canonical build
definition. MetroPT and hydraulic results must remain separate portfolio
benchmark demonstrations rather than Velora operational pages. No AWS step is
part of this sequence.

## Supporting Stage 16A.7 business-case evidence

Business-case evidence is reproducible after the governed production input and
accepted loss-accounting definition are present. It is not an input to, or a
mandatory step in, the Velora PostgreSQL/Power BI operational clean build.

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
for the two-year 2024-2025 period, not realized savings; EUR 286,954,214.88/year
is its simple annualized base, not a forecast.

## Supporting Stage 16A.8 public-source orchestration

The 14 real external source packages have a separate, explicit runner and
manifest:

- `sources/run_all_sources.ps1`
- `sources/source_pipeline_manifest.json`
- `sources/requirements.txt`

They are not steps in the Velora operational clean-database sequence. The
runner resolves from its own repository location, so callers do not need to
change directory. Use `-DryRun` to inspect all action paths and states without
executing downloads, validators, or transformations.

The source manifest explicitly routes Steps 01 and 02 despite their nonstandard
layouts. Step 01 now has the complete `download -> validate/verify -> transform`
route. Its downloader uses the recorded verified public GitHub mirror while UCI
dataset 851 remains the authoritative source; it validates and reuses the
governed Bronze CSV without network access when the file already matches. The
manifest also records Step 12 as manual acquisition, preserves Step 13's CDS
credential requirement, selects the structured Stage 6C.1 Eurostat route for
Step 14, and records the canonical and superseded Step 03/05 Silver contracts.
Existing complete Bronze inputs are reused and checksummed; partial sets stop
before acquisition rather than allowing overwrite.

## Optional real external benchmark reproduction

The following paths are accepted portfolio demonstrations but are outside the
canonical Velora operational clean build. None of their inputs, models, tables,
or outputs is required by Velora operational PostgreSQL or Power BI.

### Optional MetroPT DQ extension

After SQL DDL 008 and SQL analytics 300 exist, the external telemetry DQ
extension may be reproduced in this order:

1. `sql/ddl/010_seed_telemetry_dq_rules.sql`
2. `pipelines/postgres/run_stage7b_metropt_dq.py`
3. `sql/ddl/011_create_telemetry_dq_views.sql`
4. `sql/ddl/012_validate_telemetry_dq.sql`

This extension uses `sources/step02-telemetry/`. If applied before Gold SQL 400,
the generic Gold DQ summaries will include the MetroPT benchmark domain. The
fixed 7-domain/30-rule expectations inside SQL validation 410 describe that
combined portfolio state and are not unconditional Velora-only expectations.

### Optional MetroPT analytical benchmark

To reproduce the accepted selected alert policy:

1. Optionally inventory inputs with `scripts/inventory_telemetry_silver.py`.
2. Run `scripts/run_stage12c_metropt_anomaly.py` to recreate the fixed anomaly
   score/model and `metropt_anomaly_windows.parquet` support artifact.
3. Run `scripts/run_stage12c3_alert_policy_selection.py` to recreate the
   accepted selected-policy outputs.

`scripts/run_stage12c2_adaptive_alerting.py` is retained exploratory history and
is not required to reproduce Stage 12C.3. The Stage 12C base alert conclusion is
superseded even though its anomaly-score output remains a supporting dependency
inside this optional benchmark path.

### Optional hydraulic analytical benchmark

The real external input boundary is
`sources/step04-reliability/silver/reliability/`. Reproduce the accepted result
as follows:

1. Optionally run `scripts/profile_stage13e1_condition_monitoring.py`.
2. If `data/gold/advanced_analytics/hydraulic_condition/hydraulic_cycle_features.parquet`
   is absent, run
   `scripts/run_stage13e2_hydraulic_condition_classification.py` once to build
   that support artifact; disregard its superseded model/result conclusions.
3. Run `scripts/run_stage13e3_corrected_condition_classification.py` for the
   accepted corrected benchmark outputs.

The hydraulic feature cache, models, and outputs are not loaded into the Velora
operational PostgreSQL or Power BI layers.

## Optional and excluded validation/inventory SQL

These repository scripts are deliberately outside the mandatory validation
sequence:

| File | Classification | Why it is not mandatory |
|---|---|---|
| `sql/validation/400_inventory_stage10_sources.sql` | Optional diagnostic | Read-only development inventory of candidate Stage 10 source views; creates no object and tests no final invariant. |
| `sql/validation/500_inventory_powerbi_dimensions.sql` | Optional diagnostic | Read-only semantic-model dimension inventory used during Power BI design. |
| `sql/validation/600_inventory_stage12_analytics_sources.sql` | Optional diagnostic | Read-only discovery inventory used before Stage 12 method selection. |
| `sql/validation/610_profile_stage12_analytics_feasibility.sql` | Optional diagnostic | Historical feasibility profile, not accepted-output validation. |
| `sql/validation/621_validate_quality_reject_pchart.sql` | Optional diagnostic | Paired only with optional superseded SQL 620; SQL 622 does not depend on either file. |
| `sql/validation/700_inventory_stage13_reliability_sources.sql` | Optional diagnostic | Read-only discovery inventory used before Stage 13 reliability development. |
| `sql/validation/710_profile_stage13_reliability_feasibility.sql` | Optional diagnostic | Historical feasibility/provenance profile, not final reliability validation. |
| `sql/validation/741_validate_stage13d_reliability_trends.sql` | Superseded and excluded | Paired with superseded SQL 740; corrected SQL 743 is mandatory instead. |

SQL validation 410 remains mandatory for Gold structural/KPI checks, subject to
the conditional MetroPT DQ count caveat above. SQL 623 and SQL 743 are the
mandatory accepted replacements for the optional/superseded 621 and 741 paths.

## Accepted analytical chains

| Domain | Accepted artifact | Replaces | Provenance / BI role |
|---|---|---|---|
| Quality SPC | `sql/analytics/622_create_quality_reject_laney_pprime.sql` | Ordinary p-chart in SQL 620 | Synthetic Velora workflow; accepted primary SPC result |
| MetroPT alerting | `scripts/run_stage12c3_alert_policy_selection.py` | Stage 12C base alerts and Stage 12C.2 adaptive exploration | Real external benchmark; excluded from Velora operational BI |
| Energy anomaly | `scripts/run_stage12d_energy_anomaly.py` | No predecessor marked superseded | Synthetic Velora contextual-anomaly workflow; integrated through SQL 750 |
| Forecasting | `scripts/run_stage12e_forecasting.py` | No predecessor marked superseded | Synthetic Velora production and energy workflow; integrated through SQL 750 |
| Reliability trend | `sql/analytics/742_create_stage13d2_corrected_reliability_trends.sql` | SQL 740 | Synthetic Velora operational analytics; integrated through SQL 750 |
| Hydraulic classification | `scripts/run_stage13e3_corrected_condition_classification.py` | Stage 13E.2 classifier | Real external benchmark; excluded from Velora operational BI |

## Superseded artifacts retained for history

- `sql/analytics/620_create_quality_reject_pchart.sql` is retained as a
  diagnostic, while SQL 622 is the accepted result. SQL 620 and validation 621
  are optional because SQL 622 has no dependency on them.
- `scripts/run_stage12c_metropt_anomaly.py` and
  `scripts/run_stage12c2_adaptive_alerting.py` contain the earlier exploratory
  alert conclusions. The Stage 12C base workflow still supplies the fixed score
  artifact needed by Stage 12C.3 regeneration.
- `sql/analytics/740_create_stage13d_reliability_trends.sql` is retained but
  excluded from canonical execution; SQL 742 is accepted.
- `scripts/run_stage13e2_hydraulic_condition_classification.py` and its
  uncorrected model/result files are superseded by Stage 13E.3. Stage 13E.2 may
  be used only to recreate `hydraulic_cycle_features.parquet` if that supporting
  cache is absent.

## Current boundaries and hardening status

1. **Production first-principles limitation:** Stage 16A.5 formally resolved the
   build boundary, but it did not recover the original generator. The verified
   Silver production Parquet is the immutable governed seed. Downstream
   regeneration is reproducible from that boundary; production generation from
   documented seed/configuration alone remains unrecoverable, and the
   Bronze-to-Silver converter does not change that fact.
2. **Legacy runner incompleteness:** the Stage 4 and Stage 9 convenience runners
   still do not implement this order and remain non-canonical. Stage 16A.2
   implements the sequence in `pipelines/postgres/bootstrap_database.ps1`.
3. **Validation semantics:** resolved by Stage 16A.3 and proved by Stage 16A.10;
   mandatory SQL and Python gates propagate failure while DQ `WARN` remains
   nonfatal.
4. **Advanced loader reruns:** resolved by the transactional stable-table refresh
   implemented in Stage 16A.4 and proved by Stage 16A.10.
5. **Reliability lineage:** Stage 16A.6 source-qualifies maintenance-to-downtime
   lineage and protects failure/downtime metrics from one-to-many work-order
   multiplication. The current accepted data remains one-to-one, but no
   uniqueness constraint is imposed on the maintenance reference.
6. **Power BI reproducibility:** PBIX refresh and visual verification remain
   manual. Stage 16A.10 validated its required database-facing `gold_bi` views
   but did not edit or claim refresh of the binary.
7. **External benchmark regeneration:** MetroPT and hydraulic source acquisition
   remain outside the Velora clean database/BI sequence. The corrected hydraulic
   classifier depends on the Stage 13E.2 feature cache if it is not regenerated.

## Explicit exclusions

The canonical build and Stage 16A.10 proof do not:

- alter analytical methods, SQL calculations, DAX, datasets, models, or PBIX;
- delete or rewrite superseded artifacts;
- execute optional MetroPT or hydraulic benchmark reproduction as Velora inputs;
- automate or claim a successful refresh of the binary PBIX;
- claim realized business value or AWS deployment.
