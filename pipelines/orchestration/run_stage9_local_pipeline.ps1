param(
    [switch]$SkipReferenceLoads,
    [switch]$SkipStage7,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogDir = Join-Path $RepoRoot "logs\orchestration"
$LogFile = Join-Path $LogDir "stage9_local_pipeline_$Timestamp.log"
$ManifestFile = Join-Path $LogDir "stage9_local_pipeline_$Timestamp.json"
$SummaryFile = Join-Path $LogDir "stage9_local_pipeline_$Timestamp.summary.txt"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# Start each artifact explicitly as UTF-8 so Windows PowerShell and native tools
# do not produce mixed UTF-16/UTF-8 log output.
"" | Set-Content -Path $LogFile -Encoding UTF8

function Resolve-Psql {
    $cmd = Get-Command psql.exe -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $candidates = @(
        "C:\Program Files\PostgreSQL\18\bin\psql.exe",
        "C:\Program Files\PostgreSQL\17\bin\psql.exe",
        "C:\Program Files\PostgreSQL\16\bin\psql.exe",
        "C:\Program Files\PostgreSQL\15\bin\psql.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "psql.exe was not found on PATH or in the standard PostgreSQL installation folders."
}

$PsqlExe = Resolve-Psql

$manifest = [ordered]@{
    pipeline_name = "legacy_partial_stage9_local_pipeline"
    started_at = (Get-Date).ToString("o")
    repository_root = $RepoRoot
    psql_executable = $PsqlExe
    status = "RUNNING"
    steps = @()
}

function Write-Log {
    param([string]$Message)
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $Message"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

function Write-CommandOutput {
    param([object]$InputObject)

    if ($null -eq $InputObject) {
        return
    }

    $text = [string]$InputObject
    Write-Host $text
    Add-Content -Path $LogFile -Value $text -Encoding UTF8
}

function Add-StepResult {
    param(
        [string]$Name,
        [string]$Status,
        [datetime]$Start,
        [datetime]$End,
        [string]$Command,
        [string]$Detail = ""
    )

    $manifest.steps += [ordered]@{
        name = $Name
        status = $Status
        started_at = $Start.ToString("o")
        ended_at = $End.ToString("o")
        duration_seconds = [math]::Round(($End - $Start).TotalSeconds, 3)
        command = $Command
        detail = $Detail
    }
}

function Invoke-Step {
    param(
        [string]$Name,
        [string]$Command
    )

    $start = Get-Date
    Write-Log "START  $Name"

    if ($DryRun) {
        Write-Log "DRYRUN $Command"
        $end = Get-Date
        Add-StepResult -Name $Name -Status "DRY_RUN" -Start $start -End $end -Command $Command
        return
    }

    try {
        Push-Location $RepoRoot

        # Native tools may write non-fatal warnings to stderr. Failure is
        # determined from the process exit code, not stderr text alone.
        $oldEap = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            $output = Invoke-Expression $Command 2>&1
            $exitCode = $LASTEXITCODE

            foreach ($line in $output) {
                Write-CommandOutput $line
            }
        }
        finally {
            $ErrorActionPreference = $oldEap
        }

        if ($exitCode -ne $null -and $exitCode -ne 0) {
            throw "Command exited with code $exitCode"
        }

        Pop-Location
        $end = Get-Date
        Write-Log "PASS   $Name"
        Add-StepResult -Name $Name -Status "PASS" -Start $start -End $end -Command $Command
    }
    catch {
        if ((Get-Location).Path -ne $RepoRoot) {
            try { Pop-Location } catch {}
        }

        $end = Get-Date
        Write-Log "FAIL   $Name :: $($_.Exception.Message)"
        Add-StepResult -Name $Name -Status "FAIL" -Start $start -End $end -Command $Command -Detail $_.Exception.Message

        $manifest.status = "FAILED"
        $manifest.ended_at = (Get-Date).ToString("o")
        $manifest | ConvertTo-Json -Depth 8 | Set-Content -Path $ManifestFile -Encoding UTF8

        $passCount = @($manifest.steps | Where-Object { $_.status -eq "PASS" }).Count
        $failCount = @($manifest.steps | Where-Object { $_.status -eq "FAIL" }).Count
        @(
            "Manufacturing Intelligence Platform - Stage 9 run summary"
            "Status: FAILED"
            "Started: $($manifest.started_at)"
            "Ended: $($manifest.ended_at)"
            "Passed steps: $passCount"
            "Failed steps: $failCount"
            "Log: $LogFile"
            "Manifest: $ManifestFile"
        ) | Set-Content -Path $SummaryFile -Encoding UTF8

        throw
    }
}

function Psql-Command {
    param([string]$SqlFile)
    return "& `"$PsqlExe`" -h localhost -p 5433 -U postgres -d manufacturing_intelligence -v ON_ERROR_STOP=1 -f `"$SqlFile`""
}

Write-Log "LEGACY/PARTIAL - Stage 9 local orchestration"
Write-Log "Canonical clean builds use pipelines\postgres\bootstrap_database.ps1."
Write-Log "Repository: $RepoRoot"
Write-Log "psql:      $PsqlExe"

# Stage 4
$stage4 = "powershell -NoProfile -ExecutionPolicy Bypass -File `".\pipelines\orchestration\run_stage4_local_pipeline.ps1`""
if ($SkipReferenceLoads) {
    $stage4 += " -SkipReferenceLoads"
}
Invoke-Step -Name "Stage 4 local PostgreSQL pipeline" -Command $stage4

# Stage 5
Invoke-Step -Name "Stage 5A production/OEE views" `
    -Command (Psql-Command ".\sql\analytics\100_create_oee_views.sql")

Invoke-Step -Name "Stage 5B production loss views" `
    -Command (Psql-Command ".\sql\analytics\110_create_production_loss_views.sql")

Invoke-Step -Name "Stage 5C production benchmark views" `
    -Command (Psql-Command ".\sql\analytics\120_create_production_benchmark_views.sql")

# Stage 6
Invoke-Step -Name "Stage 6A energy views" `
    -Command (Psql-Command ".\sql\analytics\200_create_energy_views.sql")

Invoke-Step -Name "Stage 6B utility views" `
    -Command (Psql-Command ".\sql\analytics\210_create_utility_views.sql")

Invoke-Step -Name "Stage 6C energy cost views" `
    -Command (Psql-Command ".\sql\analytics\220_create_energy_cost_views.sql")

# Stage 7
if (-not $SkipStage7) {
    Invoke-Step -Name "Stage 7A structured DQ rules" `
        -Command "python .\pipelines\postgres\run_stage7a_data_quality.py"

    Invoke-Step -Name "Stage 7B MetroPT telemetry DQ" `
        -Command "python .\pipelines\postgres\run_stage7b_metropt_dq.py"
}

# Final validation
Invoke-Step -Name "Stage 5 production validation" `
    -Command (Psql-Command ".\sql\validation\120_validate_production_benchmark.sql")

Invoke-Step -Name "Stage 6 cost validation" `
    -Command (Psql-Command ".\sql\validation\220_validate_energy_cost.sql")

Invoke-Step -Name "Stage 7 structured DQ validation" `
    -Command (Psql-Command ".\sql\validation\300_validate_data_quality.sql")

Invoke-Step -Name "Stage 7 telemetry DQ validation" `
    -Command (Psql-Command ".\sql\ddl\012_validate_telemetry_dq.sql")

$manifest.status = "PASSED_PARTIAL"
$manifest.ended_at = (Get-Date).ToString("o")
$manifest | ConvertTo-Json -Depth 8 | Set-Content -Path $ManifestFile -Encoding UTF8

$passCount = @($manifest.steps | Where-Object { $_.status -eq "PASS" }).Count
$totalSeconds = [math]::Round(((Get-Date) - [datetime]$manifest.started_at).TotalSeconds, 3)

@(
    "Manufacturing Intelligence Platform - legacy/partial Stage 9 run summary"
    "Status: PASSED_PARTIAL (not a canonical clean-build PASS)"
    "Started: $($manifest.started_at)"
    "Ended: $($manifest.ended_at)"
    "Passed steps: $passCount"
    "Failed steps: 0"
    "Duration seconds: $totalSeconds"
    "PostgreSQL: localhost:5433 / manufacturing_intelligence"
    "psql: $PsqlExe"
    "Log: $LogFile"
    "Manifest: $ManifestFile"
) | Set-Content -Path $SummaryFile -Encoding UTF8

Write-Log ""
Write-Log "LEGACY/PARTIAL PIPELINE COMPLETE - not a canonical clean-build PASS"
Write-Log "Log:      $LogFile"
Write-Log "Manifest: $ManifestFile"
Write-Log "Summary:  $SummaryFile"
