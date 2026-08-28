# Installation and canonical build

## Prerequisites

- Python 3.11 or newer
- PostgreSQL with `psql`
- PowerShell 7 or Windows PowerShell 5.1
- Power BI Desktop to inspect or refresh the final PBIX
- Git

The demonstrated build used PostgreSQL 18.6. The host, port, database, user,
administrative database, and Python command are configurable.

## Install Python dependencies

Clone the repository and enter its root directory:

```powershell
git clone <repository-url>
Set-Location manufacturing-intelligence-platform
```

Install the consolidated Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

The root requirements file covers the canonical database build, source
acquisition utilities, and supported optional benchmarks.

## PostgreSQL authentication

Use standard libpq credential handling, such as a local `pgpass.conf`, or allow
the Python database steps to prompt interactively. Do not place passwords in
repository files or command examples.

The canonical runner defaults to `localhost:5433`, user `postgres`, and database
`manufacturing_intelligence`; every connection parameter can be overridden.

## Required materialized inputs

The canonical database build starts from governed materialized inputs. In
particular, it requires the hash-verified production seed at:

```text
data/silver/synthetic_enterprise/production/production_operations_2024_2025.parquet
```

Bulk public-source and generated datasets are intentionally excluded from Git.
Use the source manifests and acquisition runner where reacquisition is
supported. Industrial Utilities uses acquisition-only/no-redistribution handling,
and EU ETS requires a manually supplied workbook with no source redistribution.

Inspect source routes without downloading anything:

```powershell
& .\sources\run_all_sources.ps1 -DryRun
```

Run the required acquisition, validation, and transformation routes described
in `sources/source_pipeline_manifest.json`. ERA5-Land requires user-owned CDS
credentials and accepted provider terms. The canonical database build expects
the materialized Silver inputs listed in the [build order](reproducibility/canonical_build_order.md).

```powershell
& .\sources\run_all_sources.ps1
```

Regenerate downstream synthetic facts from the governed production seed after
their external context/reference inputs are present:

```powershell
python .\synthetic\generators\generate_downtime_events.py
python .\synthetic\generators\generate_quality_events.py
python .\synthetic\generators\generate_maintenance_work_orders.py
python .\synthetic\generators\generate_energy_utilities.py
```

## Verify governed inputs

These checks are read-only:

```powershell
python .\scripts\verify_canonical_production_seed.py
python .\scripts\verify_energy_artifact.py
python .\scripts\load_powerbi_advanced_analytics.py --validate-only
```

The canonical runner performs the same preflights before database creation or
mutation.

## Build PostgreSQL

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\pipelines\postgres\bootstrap_database.ps1 `
  -PgHost localhost `
  -PgPort 5433 `
  -PgUser postgres `
  -PgDatabase manufacturing_intelligence `
  -PgAdminDatabase postgres `
  -PythonCommand python
```

The runner creates the database, executes the complete DDL and migration chain,
loads governed facts and references, builds analytics/Gold/`gold_bi`, loads the
accepted advanced-analytics bridge, and executes all 19 mandatory fail-fast
validations.

See [canonical_build_order.md](reproducibility/canonical_build_order.md) for the
exact sequence and input boundary.

## Power BI

Open:

```text
powerbi/Velora_Manufacturing_Intelligence.pbix
```

Point its PostgreSQL connection at the built database and refresh. The retained
theme is `powerbi/theme/Velora_Manufacturing_Intelligence_Theme.json`; the
versioned screenshots show the accepted six-page report.

## Optional external benchmarks

MetroPT and hydraulic-condition analytics are separate real-data benchmark
demonstrations, not inputs to the Velora operational database.

MetroPT selected-policy reproduction:

```powershell
python .\scripts\run_metropt_anomaly_scoring.py
python .\scripts\select_metropt_alert_policy.py
```

Hydraulic condition-classification reproduction:

```powershell
python .\scripts\prepare_hydraulic_features.py
python .\scripts\run_hydraulic_condition_classification.py
```

The first hydraulic command supplies the reusable feature cache. The second
command produces the accepted class-wise chronological benchmark evidence.
