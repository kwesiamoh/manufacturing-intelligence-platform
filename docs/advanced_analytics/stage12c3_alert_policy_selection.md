# Stage 12C.3 — Alert Policy Selection

Stage 12C.2 reduced alert burden successfully, but its strict adaptive policy
detected only 2/4 known failures and none at least two hours early.

Rather than tuning against all four failure events, Stage 12C.3 uses a
time-ordered development/test split at the **alert-policy layer only**.

## Fixed anomaly model

The Isolation Forest trained in Stage 12C is not retrained.

## Policy candidates

A deliberately small pre-declared grid is evaluated:

Adaptive quantile:
- 98.5%
- 99.0%
- 99.25%
- 99.5%

Persistence:
- 2 of trailing 3 bins
- 3 of trailing 4 bins

All candidates use:
- 7-day trailing score history
- 24-hour exclusion lag
- 3-day minimum history

## Policy selection

Known failure events 1 and 2 are used only for alert-policy validation.

A candidate must preferably satisfy:
- false alert episodes/day <= 0.5
- time in alert <= 3%

Among candidates satisfying that operational budget, selection prioritizes:
1. >=2-hour early detection on validation events;
2. event detection;
3. lower false-alert burden.

## Final test

Failure events 3 and 4 are held out from policy selection and form the final
time-ordered test.

Because there are only two events in the final test, results must be reported
as small-sample evidence rather than as a precise population performance rate.

## Why this is preferable to tuning all four events

Choosing a threshold that performs best on all four known failures and then
reporting the same four failures as validation would be circular.

The 2-event validation / 2-event final-test split is imperfect because the
dataset is small, but it preserves a genuinely unseen event test for the alert
policy while keeping the underlying Isolation Forest unchanged.
