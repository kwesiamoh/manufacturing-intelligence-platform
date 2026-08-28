param(
    [string]$PgHost = "localhost",
    [int]$PgPort = 5433,
    [string]$PgDatabase = "manufacturing_intelligence",
    [string]$PgUser = "postgres",
    [switch]$SkipReferenceLoads
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")

Write-Host ""
Write-Host "LEGACY/PARTIAL - Local Stage 4 Pipeline"
Write-Host "========================================"
Write-Host "Canonical clean builds use pipelines\postgres\bootstrap_database.ps1."
Write-Host "Repository : $RepoRoot"
Write-Host "PostgreSQL : $PgHost`:$PgPort"
Write-Host "Database   : $PgDatabase"
Write-Host "User       : $PgUser"
Write-Host ""

function Run-Step {
    param(
        [string]$Name,
        [string[]]$CommandArgs
    )

    Write-Host ""
    Write-Host ">>> $Name"
    Write-Host ("-" * ($Name.Length + 4))

    & python @CommandArgs

    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

Push-Location $RepoRoot

try {
    Run-Step "Load master dimensions" @(
        ".\pipelines\postgres\load_master_dimensions.py",
        "--host", $PgHost,
        "--port", "$PgPort",
        "--dbname", $PgDatabase,
        "--user", $PgUser
    )

    Run-Step "Load synthetic operational facts" @(
        ".\pipelines\postgres\load_synthetic_facts.py",
        "--host", $PgHost,
        "--port", "$PgPort",
        "--dbname", $PgDatabase,
        "--user", $PgUser
    )

    if (-not $SkipReferenceLoads) {
        Run-Step "Load real reference and benchmark datasets" @(
            ".\pipelines\postgres\load_reference_datasets.py",
            "--host", $PgHost,
            "--port", "$PgPort",
            "--dbname", $PgDatabase,
            "--user", $PgUser
        )
    }
    else {
        Write-Host ""
        Write-Host ">>> Reference loads skipped"
        Write-Host "Use this mode for quicker operational reloads when the real benchmark tables have not changed."
    }

    Run-Step "Validate Stage 4 database" @(
        ".\pipelines\postgres\validate_stage4_database.py",
        "--host", $PgHost,
        "--port", "$PgPort",
        "--dbname", $PgDatabase,
        "--user", $PgUser
    )

    Write-Host ""
    Write-Host "===================================================="
    Write-Host "Legacy/partial Stage 4 steps completed successfully."
    Write-Host "This is not a canonical clean-build PASS."
}
finally {
    Pop-Location
}
