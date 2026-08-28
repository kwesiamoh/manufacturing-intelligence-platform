[CmdletBinding()]
param(
    [ValidateSet("All", "Acquire", "Validate", "Transform")]
    [string]$Phase = "All",
    [string[]]$Step,
    [switch]$DryRun,
    [switch]$ContinueOnError,
    [string]$ManifestPath,
    [string]$PythonCommand = "python",
    [ValidateSet("Table", "Json")]
    [string]$OutputFormat = "Table"
)

$ErrorActionPreference = "Stop"
$sourceRoot = $PSScriptRoot
$repoRoot = Split-Path -Parent $sourceRoot
if ([string]::IsNullOrWhiteSpace($ManifestPath)) {
    $ManifestPath = Join-Path $sourceRoot "source_pipeline_manifest.json"
}
$resolvedManifest = [System.IO.Path]::GetFullPath($ManifestPath)

if (-not (Test-Path -LiteralPath $resolvedManifest -PathType Leaf)) {
    throw "Source pipeline manifest not found: $resolvedManifest"
}

try {
    $manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $resolvedManifest |
        ConvertFrom-Json
}
catch {
    throw "Source pipeline manifest is invalid JSON: $resolvedManifest`n$($_.Exception.Message)"
}

if ($manifest.schema_version -ne "1.0" -or -not $manifest.steps) {
    throw "Unsupported or empty source pipeline manifest: $resolvedManifest"
}

$selectedSteps = @($manifest.steps)
if ($Step) {
    $normalized = @(
        $Step |
            ForEach-Object { $_ -split "," } |
            ForEach-Object { $_.Trim().PadLeft(2, "0") }
    )
    $selectedSteps = @($selectedSteps | Where-Object { $normalized -contains $_.step })
    $unknown = @($normalized | Where-Object { $_ -notin @($selectedSteps.step) })
    if ($unknown) {
        throw "Unknown source step(s): $($unknown -join ', ')"
    }
}

$phaseNames = if ($Phase -eq "All") {
    @("acquisition", "validation", "transformation")
}
else {
    @($Phase.ToLowerInvariant().Replace("acquire", "acquisition").Replace("validate", "validation").Replace("transform", "transformation"))
}

$results = [System.Collections.Generic.List[object]]::new()
$blockingFailure = $false

function Add-Result {
    param(
        [object]$SourceStep,
        [string]$Action,
        [string]$Mode,
        [string]$Status,
        [string]$Detail
    )
    $results.Add([pscustomobject]@{
        Step = $SourceStep.step
        Source = $SourceStep.id
        Action = $Action
        Mode = $Mode.ToUpperInvariant()
        Status = $Status
        Detail = $Detail
    })
}

function Resolve-RepoPath {
    param([string]$RelativePath)
    return [System.IO.Path]::GetFullPath((Join-Path $repoRoot $RelativePath))
}

function Get-InputState {
    param([object[]]$RequiredInputs)
    $paths = @($RequiredInputs | ForEach-Object { Resolve-RepoPath $_ })
    $existing = @($paths | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf })
    return [pscustomobject]@{
        Paths = $paths
        Existing = $existing
        Missing = @($paths | Where-Object { -not (Test-Path -LiteralPath $_ -PathType Leaf) })
        Complete = ($paths.Count -gt 0 -and $existing.Count -eq $paths.Count)
        Empty = ($existing.Count -eq 0)
    }
}

function Get-ReuseDetail {
    param([string[]]$Paths)
    $parts = foreach ($path in $Paths) {
        $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
        "$(Split-Path -Leaf $path) sha256=$hash"
    }
    return "immutable Bronze reused; " + ($parts -join "; ")
}

function Test-CdsCredentials {
    if ($env:CDSAPI_KEY -and $env:CDSAPI_URL) {
        return $true
    }
    $userProfile = [Environment]::GetFolderPath([Environment+SpecialFolder]::UserProfile)
    if ([string]::IsNullOrWhiteSpace($userProfile)) {
        return $false
    }
    return Test-Path -LiteralPath (Join-Path $userProfile ".cdsapirc") -PathType Leaf
}

function Invoke-SourceAction {
    param(
        [object]$SourceStep,
        [string]$ActionName,
        [object]$Action
    )

    $mode = [string]$Action.mode
    $required = Get-InputState @($Action.required_inputs)

    if ($mode -eq "manual_input") {
        $detail = [string]$Action.reason
        if ($required.Complete) {
            $detail += "; required materialized input is present, but acquisition remains manual"
        }
        else {
            $detail += "; missing: $($required.Missing -join ', ')"
            $script:blockingFailure = $true
        }
        Add-Result $SourceStep $ActionName $mode "MANUAL_INPUT_REQUIRED" $detail
        return
    }

    if ($mode -eq "not_implemented") {
        $status = if ($required.Complete) { "SKIPPED_INTENTIONALLY" } else { "UNAVAILABLE" }
        if ($status -eq "UNAVAILABLE" -and -not $DryRun) {
            $script:blockingFailure = $true
        }
        Add-Result $SourceStep $ActionName $mode $status ([string]$Action.reason)
        return
    }

    if ($mode -ne "automated" -and $mode -ne "automated_authenticated") {
        $script:blockingFailure = $true
        Add-Result $SourceStep $ActionName $mode "FAILED" "unsupported action mode"
        return
    }

    $verifyExistingViaScript = (
        $ActionName -eq "acquisition" -and
        $required.Complete -and
        $Action.PSObject.Properties.Name -contains "verify_existing_via_script" -and
        [bool]$Action.verify_existing_via_script
    )

    if ($ActionName -eq "acquisition" -and $required.Complete -and -not $verifyExistingViaScript) {
        $detail = if ($DryRun) {
            "immutable Bronze inputs are already present; checksum/reuse would occur during execution"
        }
        else {
            Get-ReuseDetail $required.Paths
        }
        Add-Result $SourceStep $ActionName $mode "SKIPPED_INTENTIONALLY" $detail
        return
    }

    if ($ActionName -eq "acquisition" -and -not $required.Complete -and -not $required.Empty) {
        $script:blockingFailure = $true
        Add-Result $SourceStep $ActionName $mode "FAILED" (
            "partial immutable Bronze set; refusing download/overwrite; missing: " +
            ($required.Missing -join ", ")
        )
        return
    }

    if ($ActionName -ne "acquisition" -and -not $required.Complete) {
        if (-not $DryRun) {
            $script:blockingFailure = $true
        }
        Add-Result $SourceStep $ActionName $mode "UNAVAILABLE" (
            "missing prerequisite(s): " + ($required.Missing -join ", ")
        )
        return
    }

    if ($mode -eq "automated_authenticated" -and -not (Test-CdsCredentials)) {
        if (-not $DryRun) {
            $script:blockingFailure = $true
        }
        Add-Result $SourceStep $ActionName $mode "UNAVAILABLE" (
            "CDS/ERA5 credentials are required via .cdsapirc or CDSAPI_URL/CDSAPI_KEY"
        )
        return
    }

    $scriptPath = Resolve-RepoPath ([string]$Action.script)
    if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) {
        if (-not $DryRun) {
            $script:blockingFailure = $true
        }
        Add-Result $SourceStep $ActionName $mode "UNAVAILABLE" "script missing: $scriptPath"
        return
    }

    if ($DryRun) {
        Add-Result $SourceStep $ActionName $mode "SKIPPED_INTENTIONALLY" "dry-run resolved: $scriptPath"
        return
    }

    $scriptPath = Resolve-RepoPath ([string]$Action.script)
    $workingDirectory = Resolve-RepoPath ([string]$SourceStep.package_path)
    if (-not (Test-Path -LiteralPath $workingDirectory -PathType Container)) {
        $script:blockingFailure = $true
        Add-Result $SourceStep $ActionName $mode "UNAVAILABLE" (
            "package directory missing: $workingDirectory"
        )
        return
    }
    $detail = $null
    $commandOutput = $null
    $locationPushed = $false
    try {
        Push-Location -LiteralPath $workingDirectory
        $locationPushed = $true
        if ($OutputFormat -eq "Json") {
            $commandOutput = (& $PythonCommand $scriptPath 2>&1 | Out-String).Trim()
            if ($commandOutput.Length -gt 2000) {
                $commandOutput = $commandOutput.Substring(0, 2000) + "..."
            }
        }
        else {
            & $PythonCommand $scriptPath
        }
        $exitCode = $LASTEXITCODE
    }
    catch {
        $exitCode = 1
        $detail = $_.Exception.Message
    }
    finally {
        if ($locationPushed) {
            Pop-Location
        }
    }

    if ($exitCode -eq 0) {
        $successDetail = "exit code 0"
        if ($commandOutput) { $successDetail += "; output: $commandOutput" }
        Add-Result $SourceStep $ActionName $mode "COMPLETED" $successDetail
    }
    else {
        $script:blockingFailure = $true
        if (-not $detail) {
            $detail = "exit code $exitCode"
            if ($commandOutput) { $detail += "; output: $commandOutput" }
        }
        Add-Result $SourceStep $ActionName $mode "FAILED" $detail
    }
}

foreach ($sourceStep in $selectedSteps) {
    foreach ($phaseName in $phaseNames) {
        $action = $sourceStep.$phaseName
        if ($null -eq $action) {
            Add-Result $sourceStep $phaseName "not_implemented" "SKIPPED_INTENTIONALLY" "no action declared"
            continue
        }
        Invoke-SourceAction $sourceStep $phaseName $action
        if ($blockingFailure -and -not $ContinueOnError -and -not $DryRun) {
            break
        }
    }
    if ($blockingFailure -and -not $ContinueOnError -and -not $DryRun) {
        break
    }
}

if ($OutputFormat -eq "Json") {
    @($results) | ConvertTo-Json -Depth 5
}
else {
    Write-Host ""
    Write-Host "Source orchestration summary"
    $results | Format-Table Step, Source, Action, Mode, Status, Detail -Wrap -AutoSize

    $counts = $results | Group-Object Status | Sort-Object Name
    foreach ($count in $counts) {
        Write-Host ("{0}: {1}" -f $count.Name, $count.Count)
    }
}

if ($blockingFailure -and -not $DryRun) {
    exit 1
}
exit 0
