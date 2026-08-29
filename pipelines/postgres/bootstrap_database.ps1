param(
    [string]$PgUser = "postgres",
    [string]$PgHost = "localhost",
    [int]$PgPort = 5433,
    [string]$PgDatabase = "manufacturing_intelligence",
    [string]$PgAdminDatabase = "postgres",
    [string]$PythonCommand = "python",
    [switch]$SkipDatabaseCreation,
    [switch]$PreflightOnly
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host $Title
    Write-Host ("=" * $Title.Length)
}

function Resolve-RequiredCommand {
    param(
        [string]$CommandName,
        [string]$InstallHint
    )

    $command = Get-Command $CommandName -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "$CommandName was not found. $InstallHint"
    }
    return $command.Source
}

function Assert-RequiredPath {
    param([string]$RelativePath)

    $path = Join-Path $RepoRoot $RelativePath
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Required canonical build input or executable is missing: $path"
    }
}

function Assert-AnyPath {
    param(
        [string]$Description,
        [string[]]$RelativePaths
    )

    foreach ($relative in $RelativePaths) {
        if (Test-Path -LiteralPath (Join-Path $RepoRoot $relative)) {
            return
        }
    }

    throw "Required $Description was not found. Checked: $($RelativePaths -join ', ')"
}

function Assert-MatchingFile {
    param(
        [string]$Description,
        [string]$RelativeDirectory,
        [string]$Filter,
        [switch]$Recurse
    )

    $directory = Join-Path $RepoRoot $RelativeDirectory
    if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
        throw "Required $Description directory was not found: $directory"
    }

    $matches = @(
        Get-ChildItem -LiteralPath $directory -File -Filter $Filter -Recurse:$Recurse
    )
    if ($matches.Count -eq 0) {
        throw "Required $Description was not found under $directory (filter: $Filter)"
    }
}

function Invoke-PsqlFile {
    param(
        [string]$RelativePath,
        [string]$Database = $PgDatabase,
        [hashtable]$Variables = @{},
        [string]$StepName = ""
    )

    if ([string]::IsNullOrWhiteSpace($StepName)) {
        $StepName = $RelativePath
    }
    $path = Join-Path $RepoRoot $RelativePath
    Write-Host ">>> $StepName [$RelativePath]"

    $arguments = @(
        "-h", $PgHost,
        "-p", "$PgPort",
        "-U", $PgUser,
        "-d", $Database,
        "-v", "ON_ERROR_STOP=1",
        "-P", "pager=off"
    )

    foreach ($name in ($Variables.Keys | Sort-Object)) {
        $arguments += @("-v", "$name=$($Variables[$name])")
    }
    $arguments += @("-f", $path)

    & $script:PsqlExe @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Mandatory SQL step '$StepName' ($RelativePath) failed with exit code $LASTEXITCODE"
    }
}

function Invoke-PythonFile {
    param(
        [string]$RelativePath,
        [string[]]$Arguments = @(),
        [string]$StepName = ""
    )

    if ([string]::IsNullOrWhiteSpace($StepName)) {
        $StepName = $RelativePath
    }
    $path = Join-Path $RepoRoot $RelativePath
    Write-Host ">>> $StepName [$RelativePath]"
    & $script:PythonExe $path @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Mandatory Python step '$StepName' ($RelativePath) failed with exit code $LASTEXITCODE"
    }
}

$schemaSqlFiles = @(
    "sql\ddl\001_create_dimensions.sql",
    "sql\ddl\002_create_facts.sql",
    "sql\migrations\004_add_fact_lineage.sql",
    "sql\migrations\005_add_maintenance_downtime_source_lineage.sql",
    "sql\migrations\006_create_metropt_predictive_maintenance.sql",
    "sql\ddl\003_seed_static_dimensions.sql",
    "sql\ddl\004_create_reference_tables.sql",
    "sql\ddl\005_create_loss_value_config.sql",
    "sql\ddl\006_create_energy_detail_tables.sql",
    "sql\ddl\007_create_eurostat_price_observations.sql",
    "sql\ddl\008_create_data_quality_tables.sql",
    "sql\ddl\009_seed_data_quality_rules.sql"
)

$loaderFiles = @(
    "pipelines\postgres\load_master_dimensions.py",
    "pipelines\postgres\load_synthetic_facts.py",
    "pipelines\postgres\load_reference_datasets.py",
    "pipelines\postgres\load_energy_details.py",
    "pipelines\postgres\load_eurostat_electricity_prices.py",
    "pipelines\postgres\load_metropt_predictive_maintenance.py"
)

$coreAnalyticsSqlFiles = @(
    "sql\analytics\100_create_oee_views.sql",
    "sql\analytics\110_create_production_loss_views.sql",
    "sql\analytics\120_create_production_benchmark_views.sql",
    "sql\analytics\200_create_energy_views.sql",
    "sql\analytics\210_create_utility_views.sql",
    "sql\analytics\220_create_energy_cost_views.sql"
)

$reportingSqlFiles = @(
    "sql\analytics\300_create_data_quality_views.sql",
    "sql\analytics\400_create_gold_models.sql",
    "sql\analytics\410_create_powerbi_compat_views.sql",
    "sql\analytics\622_create_quality_reject_laney_pprime.sql",
    "sql\analytics\720_create_reliability_kpis.sql",
    "sql\analytics\730_create_failure_downtime_analysis.sql",
    "sql\analytics\742_create_reliability_trends.sql",
    "sql\analytics\760_create_metropt_predictive_maintenance_views.sql"
)

$validationSqlFiles = @(
    "sql\admin\010_verify_schema.sql",
    "sql\validation\020_dimension_counts.sql",
    "sql\validation\030_synthetic_fact_counts.sql",
    "sql\validation\040_reference_counts.sql",
    "sql\validation\050_database_validation.sql",
    "sql\validation\100_validate_oee_views.sql",
    "sql\validation\110_validate_production_loss.sql",
    "sql\validation\120_validate_production_benchmark.sql",
    "sql\validation\200_validate_energy_views.sql",
    "sql\validation\210_validate_utility_views.sql",
    "sql\validation\220_validate_energy_cost.sql",
    "sql\validation\300_validate_data_quality.sql",
    "sql\validation\410_validate_gold_models.sql",
    "sql\validation\623_validate_quality_reject_laney_pprime.sql",
    "sql\validation\721_validate_reliability_kpis.sql",
    "sql\validation\731_validate_failure_downtime_analysis.sql",
    "sql\validation\743_validate_reliability_trends.sql",
    "sql\validation\761_validate_metropt_predictive_maintenance.sql",
    "sql\validation\415_validate_can_air_powerbi.sql",
    "sql\validation\751_validate_powerbi_advanced_analytics_views.sql"
)

$productionBoundaryPaths = @(
    "config\canonical_production_seed.json",
    "scripts\verify_canonical_production_seed.py",
    "data\silver\synthetic_enterprise\production\production_operations_2024_2025.parquet",
    "config\energy_artifact_manifest.json",
    "scripts\verify_energy_artifact.py",
    "scripts\load_powerbi_advanced_analytics.py",
    "pipelines\postgres\load_metropt_predictive_maintenance.py",
    "data\silver\synthetic_enterprise\telemetry\metropt_enterprise_telemetry.parquet",
    "data\gold\advanced_analytics\metropt_predictive_maintenance\metropt_enterprise_warning_events.csv",
    "data\gold\advanced_analytics\metropt_predictive_maintenance\metropt_predictive_maintenance_kpis.csv",
    "pipelines\postgres\connection_auth.py"
)

$requiredRepositoryPaths = @(
    "sql\admin\000_create_database.sql",
    "pipelines\postgres\run_data_quality.py",
    "pipelines\postgres\validate_database.py",
    "scripts\load_powerbi_advanced_analytics.py",
    "sql\analytics\750_create_powerbi_advanced_analytics_views.sql",
    "data_model\source_mapping\source_dataset_seed.csv",
    "data_model\dimensions\fictional_site_registry.csv",
    "data_model\dimensions\area_master.csv",
    "data_model\dimensions\product_portfolio.csv",
    "data_model\dimensions\shift_master.csv",
    "data_model\dimensions\line_master.csv",
    "data_model\dimensions\equipment_master.csv",
    "data_model\dimensions\failure_reason_seed.csv",
    "data\silver\synthetic_enterprise\downtime\downtime_events_2024_2025.parquet",
    "data\silver\synthetic_enterprise\quality\quality_events_2024_2025.parquet",
    "data\silver\synthetic_enterprise\maintenance\maintenance_work_orders_2024_2025.parquet",
    "data\silver\synthetic_enterprise\energy\line_energy_utility_2024_2025.parquet",
    "data\silver\synthetic_enterprise\energy\site_energy_2024_2025.parquet",
    "sources\eurostat-energy-prices\silver\eurostat_energy_prices\nrg_pc_205__six_site_countries_2024_2025.parquet",
    "data\gold\advanced_analytics\energy_anomaly\energy_anomaly_shift_monitoring_2025.parquet",
    "data\gold\advanced_analytics\forecasting\daily_site_forecast_holdout_2025.parquet"
) + $schemaSqlFiles + $loaderFiles + $coreAnalyticsSqlFiles +
    $reportingSqlFiles + $validationSqlFiles

Write-Section "Canonical Velora operational build preflight"

$script:PsqlExe = Resolve-RequiredCommand -CommandName "psql" `
    -InstallHint "Install PostgreSQL or add its bin directory to PATH."
$script:PythonExe = Resolve-RequiredCommand -CommandName $PythonCommand `
    -InstallHint "Install Python or pass -PythonCommand with its executable path."

foreach ($relative in $productionBoundaryPaths) {
    Assert-RequiredPath -RelativePath $relative
}
Invoke-PythonFile -RelativePath "scripts\verify_canonical_production_seed.py" `
    -Arguments @("--manifest", "config\canonical_production_seed.json") `
    -StepName "Canonical production seed verification"
Invoke-PythonFile -RelativePath "scripts\verify_energy_artifact.py" `
    -StepName "Governed energy artifact verification"
Invoke-PythonFile -RelativePath "scripts\load_powerbi_advanced_analytics.py" `
    -Arguments @("--validate-only") `
    -StepName "Accepted energy-anomaly and forecasting input verification"
Invoke-PythonFile -RelativePath "pipelines\postgres\load_metropt_predictive_maintenance.py" `
    -Arguments @("--validate-only") `
    -StepName "Governed enterprise telemetry input verification"

foreach ($relative in ($requiredRepositoryPaths | Sort-Object -Unique)) {
    Assert-RequiredPath -RelativePath $relative
}

Assert-MatchingFile -Description "ITAC assessment Parquet" `
    -RelativeDirectory "sources\industrial-energy-assessment\silver\itac" `
    -Filter "*__assess.parquet"
Assert-MatchingFile -Description "ITAC recommendation Parquet" `
    -RelativeDirectory "sources\industrial-energy-assessment\silver\itac" `
    -Filter "*__recc.parquet"
Assert-AnyPath -Description "FMUCD Silver Parquet" -RelativePaths @(
    "sources\fmucd-maintenance\silver\fmucd_maintenance.parquet",
    "sources\fmucd-maintenance\data\silver\fmucd_maintenance.parquet"
)
Assert-AnyPath -Description "StatCan water Silver Parquet" -RelativePaths @(
    "sources\industrial-water\silver\statcan_industrial_water\38100056.parquet",
    "sources\industrial-water\data\silver\statcan_industrial_water\38100056.parquet"
)
Assert-MatchingFile -Description "EIA MECS Silver Parquet" `
    -RelativeDirectory "sources\manufacturing-fuels\silver" -Filter "*.parquet" -Recurse
Assert-AnyPath -Description "EU ETS Silver Parquet" -RelativePaths @(
    "sources\eu-ets-emissions\silver\eea_eu_ets\sheet1.parquet",
    "sources\eu-ets-emissions\data\silver\eea_eu_ets\sheet1.parquet"
)
Assert-MatchingFile -Description "Eurostat Silver Parquet" `
    -RelativeDirectory "sources\eurostat-energy-prices\silver" `
    -Filter "*.parquet" -Recurse

Write-Host "Repository: $RepoRoot"
Write-Host "PostgreSQL: $PgHost`:$PgPort / $PgDatabase"
Write-Host "PostgreSQL user: $PgUser"
Write-Host "psql: $script:PsqlExe"
Write-Host "Python: $script:PythonExe"
Write-Host "Verified governed production input: data\silver\synthetic_enterprise\production\production_operations_2024_2025.parquet"
Write-Host "Accepted energy-anomaly and forecasting outputs are materialized inputs; models will not be retrained."
Write-Host "Governed MetroPT-informed enterprise telemetry is a materialized canonical input; its source model will not be rerun."
Write-Host "Preflight passed. No database changes have been made yet."

if ($PreflightOnly) {
    Write-Host "Preflight-only mode requested. No database connection or mutation was attempted."
    return
}

if (-not $SkipDatabaseCreation) {
    Write-Section "Database creation"
    Invoke-PsqlFile -RelativePath "sql\admin\000_create_database.sql" `
        -Database $PgAdminDatabase -Variables @{ db_name = $PgDatabase }
}
else {
    Write-Host ""
    Write-Host "Database creation skipped by request; subsequent steps require $PgDatabase to exist."
}

Write-Section "Schema and configuration"
foreach ($relative in $schemaSqlFiles) {
    Invoke-PsqlFile -RelativePath $relative
}

$connectionArguments = @(
    "--host", $PgHost,
    "--port", "$PgPort",
    "--dbname", $PgDatabase,
    "--user", $PgUser
)

Write-Section "Dimensions, facts, references, and supplemental data"
foreach ($relative in $loaderFiles) {
    Invoke-PythonFile -RelativePath $relative -Arguments $connectionArguments
}

Write-Section "Database enforcing validation"
Invoke-PythonFile -RelativePath "pipelines\postgres\validate_database.py" `
    -Arguments $connectionArguments -StepName "Database enforcing validation"

Write-Section "Production, energy, utility, and cost analytics"
foreach ($relative in $coreAnalyticsSqlFiles) {
    Invoke-PsqlFile -RelativePath $relative
}

Write-Section "Enterprise data-quality execution and reporting"
Invoke-PythonFile -RelativePath "pipelines\postgres\run_data_quality.py" `
    -Arguments $connectionArguments -StepName "Enterprise data-quality execution"
Invoke-PsqlFile -RelativePath "sql\analytics\300_create_data_quality_views.sql"

Write-Section "Gold, Power BI compatibility, quality, and reliability"
foreach ($relative in ($reportingSqlFiles | Where-Object {
    $_ -ne "sql\analytics\300_create_data_quality_views.sql"
})) {
    Invoke-PsqlFile -RelativePath $relative
}

Write-Section "Advanced-analytics Power BI bridge"
Invoke-PythonFile -RelativePath "scripts\load_powerbi_advanced_analytics.py" `
    -Arguments $connectionArguments
Invoke-PsqlFile -RelativePath "sql\analytics\750_create_powerbi_advanced_analytics_views.sql"

Write-Section "Final canonical validation queries"
foreach ($relative in $validationSqlFiles) {
    Invoke-PsqlFile -RelativePath $relative
}

Write-Section "Canonical Velora operational build complete"
Write-Host "Database: $PgHost`:$PgPort / $PgDatabase"
Write-Host "Optional real-source MetroPT model and hydraulic benchmark reproduction was not executed."
Write-Host "Power BI Desktop refresh and visual verification remain manual."
