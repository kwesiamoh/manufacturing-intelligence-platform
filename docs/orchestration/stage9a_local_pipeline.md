# Stage 9A — Local ingestion and orchestration

## Purpose

Stage 9A turns the existing local manufacturing-intelligence build into a controlled repeatable pipeline.

It does not replace the existing scripts.

It calls them in sequence and adds:

- central execution order;
- stop-on-failure behavior;
- timestamped logging;
- run manifest;
- duration per step;
- PASS/FAIL status;
- optional skip switches.

## Execution sequence

1. Stage 4 PostgreSQL build/load pipeline
2. Stage 5 production/OEE/loss analytics
3. Stage 6 energy/utilities/cost analytics
4. Stage 7 structured data quality
5. Stage 7 MetroPT telemetry quality
6. final validation scripts

## Why Stage 4 remains a child pipeline

Stage 4 already has a repeatable runner.

Stage 9 intentionally reuses it rather than duplicating the load logic.

## Logging

Logs are written to:

`logs/orchestration/`

Each run creates:

- `.log` execution log
- `.json` run manifest

The manifest records:
- pipeline name;
- start/end time;
- each step;
- command;
- duration;
- status.

## Failure handling

The pipeline stops immediately when a command fails.

The manifest is still written with:

`status = FAILED`

This prevents later analytics from running on an incomplete database build.

## Switches

### Skip reference loads

```powershell
.\pipelines\orchestration\run_stage9_local_pipeline.ps1 -SkipReferenceLoads
```

Useful after the large real reference tables are already loaded.

### Skip Stage 7

```powershell
.\pipelines\orchestration\run_stage9_local_pipeline.ps1 -SkipStage7
```

Useful for a quick analytics rebuild.

### Dry run

```powershell
.\pipelines\orchestration\run_stage9_local_pipeline.ps1 -DryRun
```

Prints the execution plan without running the commands.

## AWS mapping

This local orchestrator is the executable reference implementation for the future AWS target.

A later AWS deployment could map:
- steps to Glue jobs / Python jobs;
- sequencing to Step Functions;
- logs to CloudWatch;
- manifests to S3.

The business logic does not need to change.
