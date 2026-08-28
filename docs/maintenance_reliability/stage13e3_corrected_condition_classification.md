# Stage 13E.3 — Corrected Hydraulic Condition Classification

## Why Stage 13E.2 was revised

The Stage 13E.2 global chronological holdout exposed strong temporal class
clustering.

Examples:

- the cooler holdout contained only the 100% condition class;
- the valve stable-cycle subset contained only the 100% class;
- pump and accumulator models matched their majority baselines despite high
  ordinary accuracy.

Those results are not suitable multiclass performance evidence.

## Stable flag

The original Stage 13E.2 design also filtered the four physical-condition
targets to `stable_flag = 1`.

That restriction is removed.

The source provides condition labels for all 2,205 cycles. `stable_flag` is
retained as its own classification target and is not used as a blanket
exclusion rule for the other targets.

## Corrected validation

For each target class independently:

1. sort cycles by `cycle_id`;
2. earliest 80% of that class are training data;
3. latest 20% are holdout data.

This guarantees that every known condition class appears in both train and
holdout while retaining temporal order within each class.

This is a condition-classification benchmark split. It is not a forward
calendar forecast.

## Primary metrics

- macro F1
- balanced accuracy

Ordinary accuracy is secondary because several targets are imbalanced.

A majority-class baseline is reported for every target.

## Run

Stage 13E.2 must have been run once already so that
`hydraulic_cycle_features.parquet` exists.

Then run:

```powershell
python .\scripts\run_stage13e3_corrected_condition_classification.py
```
