# Stage 9B orchestration finalization

Stage 9 provides a repeatable local orchestration layer for the Manufacturing Intelligence Platform.

## Implemented locally

The local runner executes the existing platform in dependency order:

1. Stage 4 structured PostgreSQL loading and validation
2. Stage 5 production, OEE, loss and benchmark analytical views
3. Stage 6 energy, utility and cost analytical views
4. Stage 7 structured and telemetry data-quality checks
5. final SQL validation gates

The runner supports:

- `-SkipReferenceLoads` for faster repeat runs when external benchmark tables have not changed
- `-SkipStage7` for targeted development runs
- `-DryRun` for command inspection without execution
- stop-on-failure behavior
- timestamped UTF-8 execution logs
- JSON run manifests
- concise text run summaries

## Run command

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\pipelines\orchestration\run_stage9_local_pipeline.ps1 -SkipReferenceLoads
```

## Run artifacts

Each run writes files under:

`logs/orchestration/`

The three artifacts are:

- `stage9_local_pipeline_<timestamp>.log`
- `stage9_local_pipeline_<timestamp>.json`
- `stage9_local_pipeline_<timestamp>.summary.txt`

The JSON manifest is the machine-readable execution record. The summary file is intended for quick inspection and portfolio evidence.

## Failure behavior

The runner does not interpret stderr text alone as a failure because Python and native command-line tools may emit warnings there. A step fails when the invoked process returns a non-zero exit code or PowerShell raises a terminating error.

## Scope

This is a local orchestration implementation. It is not an AWS deployment and should not be described as one.
