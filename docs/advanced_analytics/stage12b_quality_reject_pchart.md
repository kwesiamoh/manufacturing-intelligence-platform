# Stage 12B — Quality Reject-Proportion SPC

## Purpose

This stage adds a statistically appropriate attribute-control-chart workflow to
the manufacturing portfolio.

The enterprise quality table does not contain continuous measurement values or
specification limits, so X-bar/R, Individuals, Cp, and Cpk analyses would not
be supported by the available enterprise integration data.

Instead, Stage 12B uses the production reject proportion:

\[
p_i = \frac{\text{reject units}_i}{\text{actual units}_i}
\]

for each production shift.

## Chart design

- Chart type: p-chart
- Subgroup: production shift
- Segmentation: site + line + product
- Baseline period: 2024
- Monitoring period: 2025
- Center line: pooled 2024 reject proportion for each site/line/product
- Limits: 3-sigma binomial p-chart limits adjusted for each subgroup size

For subgroup size \(n_i\) and baseline reject proportion \(\bar p\):

\[
\sigma_i = \sqrt{\frac{\bar p(1-\bar p)}{n_i}}
\]

\[
UCL_i = \min(1,\bar p + 3\sigma_i)
\]

\[
LCL_i = \max(0,\bar p - 3\sigma_i)
\]

## Why 2024 and 2025 are separated

The 2024 observations form the fixed historical baseline. The resulting center
line and limits are then applied to 2025 observations.

This avoids estimating the monitoring limits from the same 2025 observations
that are being evaluated.

## Status interpretation

- `ABOVE_UCL`: unusually high reject proportion relative to the 2024 baseline.
- `BELOW_LCL`: unusually low reject proportion; statistically unusual, but
  operationally this may represent improvement rather than deterioration.
- `IN_CONTROL`: within the calculated 3-sigma limits.
- `NO_BASELINE`: no matching 2024 site/line/product baseline.

A control limit is not a product specification limit. A process can be
statistically stable and still perform poorly against business requirements,
and vice versa.

## Provenance limitation

The source is `SYNTHETIC_ENTERPRISE`, identified in `dim_source_dataset` as:

- source: Fictional Beverage Enterprise Integration Layer
- integration role: SYNTHETIC_INTEGRATION
- real data: false
- reference period: 2024-2025

Therefore the SPC results demonstrate the workflow and interpretation on the
fictional six-site enterprise model. They must not be described as measured
beverage-plant process evidence.

## Database object

`analytics.vw_quality_reject_pchart`

The view is Power-BI-ready and includes:
- subgroup reject proportion
- fixed baseline center line
- sample-size-adjusted LCL/UCL
- standardized z-score
- control status
- special-cause flag
- explicit source/provenance fields

## Run order

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
  -h localhost -p 5433 -U postgres `
  -d manufacturing_intelligence `
  -f .\sql\analytics\620_create_quality_reject_pchart.sql

& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
  -h localhost -p 5433 -U postgres `
  -d manufacturing_intelligence `
  -f .\sql\validation\621_validate_quality_reject_pchart.sql
```

The validation output should be reviewed before any Power BI visual is added.
