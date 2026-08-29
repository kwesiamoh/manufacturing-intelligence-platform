# Analytics Methodology and Limitations

## Purpose

This document describes the accepted analytical methods used in the Manufacturing Performance & Energy Intelligence Platform and the limitations that apply to each result.

The integrated operating model represents the fictional **Velora Beverage Group**. Public industrial datasets used for benchmarking are kept separate from the Velora operating history.

The accepted analytical period for the integrated enterprise model is **2024-01-01 through 2025-12-31**.

---

## Manufacturing performance

Manufacturing performance is calculated from the integrated production and downtime model at shift, line, site, and enterprise levels.

Primary reporting measures include:

- production output
- availability
- performance
- quality
- overall equipment effectiveness (OEE)
- downtime
- operating loss
- site and line comparisons
- technical opportunity

The accepted site-level OEE values are:

| Site | OEE |
|---|---:|
| Dortmund, Germany | 87.86% |
| Rotterdam, Netherlands | 86.76% |
| Lyon, France | 86.31% |
| Brno, Czech Republic | 84.81% |
| Zaragoza, Spain | 83.96% |
| Wrocław, Poland | 82.94% |

These figures are model-derived from the governed synthetic enterprise history. They should not be interpreted as observed OEE from real Velora plants.

---

## Quality statistical process control

### Method selection

Reject-rate SPC uses a **Laney p′ chart** because an ordinary p-chart produces excessive special-cause signalling for the substantially overdispersed subgroup population.

Laney p′ retains the p-chart structure while adjusting the control limits using a dispersion correction estimated from standardized subgroup behaviour.

### Analytical phases

The accepted quality-control implementation uses:

- **2024** as the baseline period
- **2025** as the monitoring period

Monitoring subgroups are classified as:

- `IN_CONTROL`
- `ABOVE_UCL`
- `BELOW_LCL`

The accepted analytical object is:

```text
analytics.vw_quality_reject_laney_pprime
```

### Validation

SQL 623 validates the accepted Laney p′ result.

SQL 623 materializes the accepted Laney view once into a session-local temporary table before performing validation checks. This avoids repeated expansion of the computationally expensive nested view while preserving:

- Laney calculations
- dispersion correction
- control limits
- thresholds
- subgroup classifications
- accepted analytical outputs

### Limitation

The Laney p′ method is appropriate for the modelled reject-rate population, but it has not been validated against an observed Velora production process because Velora is fictional.

The result should therefore be interpreted as a statistically controlled portfolio implementation rather than evidence of deployed industrial SPC.

---

## Production forecasting

### Objective

The production forecasting model estimates the next site-day production value using historical and contextual manufacturing information.

### Model

The accepted model is a **Histogram-Based Gradient Boosting Regressor**.

### Evaluation design

The final evaluation uses a rolling **one-day-ahead** forecasting setup.

The retained holdout period is:

```text
2025-11-02 through 2025-12-31
```

This covers 60 dates across six sites.

The final Power BI bridge contains:

- 360 production forecast rows
- 360 energy forecast rows

### Accepted production results

| Metric | Result |
|---|---:|
| MAE | 28,869 units |
| RMSE | 35,870.88 units |
| R² | 0.9865 |
| MAPE | 0.72% |

### Interpretation

The production model performs strongly on the retained holdout.

However, the final evaluation is **not** a recursive 60-day forecast. Each prediction is a rolling one-day-ahead estimate.

Model selection and final reporting also used the same final holdout period. This weakens the claim that the reported performance represents a completely untouched final test set.

The result should therefore be presented as a strong portfolio forecasting demonstration rather than production-grade model validation.

---

## Energy forecasting

### Objective

The energy forecasting model estimates next-day site electricity consumption.

### Model

The accepted model is also a **Histogram-Based Gradient Boosting Regressor**.

### Accepted results

| Metric | Result |
|---|---:|
| MAE | 154.18 kWh |
| RMSE | 189.11 kWh |
| R² | 0.7570 |
| MAPE | 0.51% |

### Interpretation

The model provides useful short-horizon forecasting for the governed synthetic energy population.

The same evaluation limitation applies as for production forecasting:

- the model is evaluated as rolling one-day-ahead forecasting
- the 60-day period is a holdout window, not a recursive multi-step forecast
- model selection and final reporting used the same holdout period

---

## Contextual energy anomaly detection

### Objective

The energy anomaly model estimates expected electricity consumption from operating context and flags unusually high or low residuals.

### Monitoring population

The accepted 2025 monitoring population contains:

- 32,850 shift observations
- 254 high-energy anomalies
- 282 low-energy anomalies

High anomalies represent approximately **0.77%** of the monitoring population.

Low anomalies represent approximately **0.86%**.

The accepted high-anomaly excess electricity total is approximately:

```text
1,220.89 kWh
```

### Model performance

The contextual expected-energy model achieved approximately:

| Metric | Result |
|---|---:|
| MAE | 0.722 kWh |
| RMSE | 1.265 kWh |
| R² | 0.9996 |
| MAPE | 0.0422% |

### Limitation

These metrics are unusually strong because the synthetic electricity target was generated from relationships involving production variables that are also informative to the anomaly model.

The target-generation process and predictor structure are therefore partly circular.

For that reason:

- the anomalies are contextual residual extremes
- they are **not** labeled equipment faults
- the model is **not** validated as a real-plant fault detector
- the very high predictive fit should not be generalized to live industrial data

The model is best interpreted as a contextual anomaly-detection demonstration.

---

## Energy and utility modelling

The enterprise energy model combines:

- line production electricity
- line idle electricity
- site auxiliary electricity
- selected utility consumption
- operating-context relationships

Accepted enterprise electricity reconciliation for 2024–2025:

| Metric | Value |
|---|---:|
| Line production electricity | 112.707 GWh |
| Line idle electricity | 0.913 GWh |
| Total line electricity | 113.620 GWh |
| Site auxiliary electricity | 19.219 GWh |
| Total site electricity | 132.839 GWh |
| Weighted site electricity intensity | 7.579 kWh / 1,000 units |

### Compressed air

Accepted compressed-air totals are:

| Production type | Total |
|---|---:|
| PET operations | 331.231 million Nm³ |
| CAN operations | 12.805 million Nm³ |
| Enterprise total | 344.036 million Nm³ |

Canning lines use the governed design assumption:

```text
5.0 Nm³ compressed air / 1,000 cans
```

This is a portfolio modelling assumption and not measured Velora utility data.

### Limitation

The energy model is suitable for manufacturing-intelligence analysis but should not be interpreted as an engineering utility-sizing or process-design model.

Some electricity and utility relationships are governed assumptions rather than field measurements.

---

## Reliability and maintenance

### Corrective-failure population

The accepted reliability population is based on corrective maintenance records linked to source-qualified downtime events.

Accepted values:

| Metric | Value |
|---|---:|
| Corrective failures | 46,670 |
| Corrective downtime | 14,856.652017 h |
| Repair hours | 13,207.527188 h |
| Weighted MTTR | 0.282998226 h |
| Monthly site-line rows | 720 |
| Analysis months | 24 |

The final lineage validation found:

- 0 ambiguous source-qualified links
- 0 downtime multiplication

### Failure-event grain

The reliability model distinguishes work-order grain from downtime-event grain.

Corrective failure counts are based on source-qualified failure events, while repair hours are aggregated from linked work orders.

This prevents one downtime event from being counted multiple times when maintenance records are joined.

### MTBF interpretation

Two different MTBF-style quantities appear in the project and should not be mixed:

1. **Equipment-level operating MTBF proxy**  
   Averaged across equipment populations and approximately 97.93 h in the accepted analytical output.

2. **Power BI aggregate operating-hours MTBF proxy**  
   Calculated as total line operating hours divided by total corrective failures and approximately 9.74 h.

These are different aggregations and are not interchangeable.

### Limitation

The reliability analysis is based on synthetic enterprise operations and modeled maintenance links.

It demonstrates reliability KPI design and lineage control, but it is not validated against real Velora CMMS or historian data.

---

## MetroPT compressor telemetry and predictive maintenance

### Purpose

MetroPT-3 supplies 1,516,948 real measurements from an industrial compressor Air Production Unit. The immutable Bronze records, standardized Silver telemetry, and four published failure windows retain UCI provenance and are not Velora operational observations.

### Causal features and evaluation design

Telemetry is aggregated into five-minute windows. Features use only current and trailing observations and include pressure, oil-temperature, and motor-current levels; trailing deviations; one-hour slopes; pressure relationships; and the accepted Isolation Forest anomaly score. No feature uses observations after its prediction timestamp.

The real predictive-warning experiment evaluates 2-, 4-, and 6-hour horizons. Failure event 1 supplies the positive training episode, event 2 is the chronological validation event, and events 3-4 form the later test period. A class-weighted logistic-regression candidate is compared with the accepted adaptive anomaly baseline:

```text
q0.9850_3of4
```

### Real MetroPT result

- selected real policy: adaptive anomaly baseline `q0.9850_3of4`
- selected evaluation horizon: 2 hours
- held-out fault events warned: 1 of 2
- median warning lead: 0.67 hours
- precision: 0.143
- recall: 0.500
- false alerts: 6, or 0.068 per operating day
- supervised logistic candidate: no validation or test warnings

### Interpretation

The real data supports anomaly/fault-event monitoring and a limited short-lead warning observation. It does not demonstrate reliable two-, four-, or six-hour advance prediction.

### MetroPT-informed synthetic enterprise result

The governed enterprise adaptation maps the compressor behavior to `SITE-DE-01-U-AIR-01`, shifts source timestamps by four years into the 2024 enterprise calendar, and retains the source timestamp on every row. Controlled six-hour degradation ramps add explicitly synthetic changes in oil temperature, motor current, and reservoir pressure.

The selected six-hour condition policy warned all four synthetic scenario events, with 5.83 hours median lead, precision and recall of 1.0, and zero false alerts. These values demonstrate the controlled scenario design; they are not measured MetroPT predictive performance.

Lineage fields identify the source as `EXTERNAL_REAL`, the scenario as `SYNTHETIC_ENTERPRISE_ADAPTATION`, the transformation basis as `METROPT_INFORMED`, and the degradation signal as `SYNTHETIC_CONTROLLED`.

The Gold detail view can expose the nearest existing maintenance work order on
the mapped compressor asset within seven days after fault onset. No such work
orders exist in the accepted maintenance history for these four scenario
events, so the integration leaves that context null rather than fabricating it.

### Limitation

Only four independent source failure events exist, and the retained events have been inspected during analytical review. The chronological evaluation is therefore small-sample evidence rather than a fully untouched lifecycle test. The synthetic scenario validates integration and decision-support semantics, not real-world model generalization.

---

## External hydraulic-condition benchmark

### Purpose

The hydraulic-condition dataset is used as a standalone benchmark for chronological condition classification.

It is not integrated into Velora operating history.

### Evaluation design

The accepted evaluation uses chronological 80/20 splitting within class.

The task is classification, not remaining-useful-life prediction or forward prognostics.

### Accepted F1 scores

| Target | F1 |
|---|---:|
| Cooler | 1.000 |
| Valve | 0.604 |
| Pump | 0.924 |
| Accumulator | 0.532 |
| Stable condition | 0.805 |

### Interpretation

The benchmark demonstrates classification across multiple equipment-condition targets with materially different difficulty.

It should not be presented as a predictive-maintenance forecasting result.

---

## Data quality

The canonical build contains **29 active enterprise DQ rules**.

Accepted clean-build result:

| Status | Rules |
|---|---:|
| PASS | 28 |
| WARN | 1 |
| FAIL | 0 |

The framework preserves explicit semantics:

- PASS: successful
- WARN: nonfatal
- FAIL: fail-fast

The established score is `1 - failed rows / evaluated rows`. Across 2,473,157
evaluated rows and 248 failed rows, the enterprise result is **99.9900%**.

The `telemetry` domain contains five rules covering required-field
completeness, equipment/timestamp uniqueness, enterprise equipment mapping,
governed lineage, and source-supported five-minute cadence. Four rules pass.
The cadence rule evaluates 42,597 consecutive intervals and reports 248
non-five-minute intervals as `WARN`, yielding a **99.8836%** telemetry-domain
score. The maximum retained gap is 48 hours 50 minutes. These gaps reflect
source availability and non-operating periods; the workflow does not fabricate
missing observations.

Untouched MetroPT observations remain external real source data. The governed
synthetic enterprise adaptation participates in enterprise DQ. Compressor
faults, controlled degradation, anomaly scores, and warning states are
operating or analytical signals, not DQ defects. No sensor plausibility rule is
asserted because the repository does not govern defensible physical limits for
every sensor.

---

## Related evidence

- [Business case](../business_case/business_case.md)
- [Canonical build order](../reproducibility/canonical_build_order.md)
- [Clean-build proof](../reproducibility/clean_build_proof.md)
- [KPI definitions](../kpi_definitions/manufacturing_kpis.md)
