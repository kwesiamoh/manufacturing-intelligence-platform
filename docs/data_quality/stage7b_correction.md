# Stage 7B correction

The first Stage 7B run exposed a classification problem in the DQ script.

## What was wrong

The Silver MetroPT columns are lowercase, but the original discrete-channel exclusion list used uppercase names.

As a result:
- COMP/status channels were incorrectly treated as continuous analog sensors;
- `year`, `month`, and `unnamed_0` were also included in frozen-signal analysis.

This inflated the frozen-signal result.

The first-difference MAD spike rule was also too sensitive for the high-frequency analog signals and produced a very large number of candidates.

## Corrected channel classification

Analog:
- tp2
- tp3
- h1
- dv_pressure
- reservoirs
- oil_temperature
- motor_current

Discrete/state:
- comp
- dv_eletric
- towers
- mpg
- lps
- pressure_switch
- oil_level

Event/counter:
- caudal_impulses

Metadata:
- unnamed_0
- year
- month

Only analog channels are used for frozen and spike screening.

## Spike diagnostic

Spike screening is now diagnostic only.

For each analog channel it reports first differences in the extreme empirical tails:
- below the 0.01 percentile
- above the 99.99 percentile

These are investigation candidates, not errors and not values to remove automatically.

## Gap result

The 363 cadence gaps from the first run remain a valid finding because timestamp classification was correct.
