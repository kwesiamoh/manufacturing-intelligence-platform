# Business Case

## Executive proposition

The Manufacturing Intelligence Platform demonstrates how production, quality,
energy, maintenance, telemetry, and data-quality information can be integrated
into one governed analytical environment.

A production implementation would aim to improve:

- operational visibility;
- loss prioritization;
- energy performance;
- maintenance decision support;
- data-quality control;
- planning and forecasting.

The current portfolio proves the analytical and architectural workflow. It does
not prove a future organization's realized financial benefit.

## Two-year modeled technical opportunity (2024-2025)

Within the synthetic six-site enterprise, the modeled technical opportunity
across the full 2024-2025 two-year analysis period is:

**€573,908,429.76**

Site-level modeled opportunity:

| Site | Technical opportunity |
|---|---:|
| Poland | €129,584,008.89 |
| Spain | €120,983,512.89 |
| Germany | €91,639,402.07 |
| Czechia | €83,522,159.59 |
| France | €75,401,655.38 |
| Netherlands | €72,777,690.94 |
| **Total** | **€573,908,429.76** |

This value is useful for demonstrating loss ranking and prioritization. It must
not be interpreted as recoverable cash without validating the underlying
economic assumptions against a real plant. The machine-readable evidence is
[`technical_opportunity_2024_2025.csv`](../../data/gold/business_case/technical_opportunity_2024_2025.csv),
generated and reconciled by
[`generate_business_case_opportunity_evidence.py`](../../scripts/generate_business_case_opportunity_evidence.py)
against `public.vw_site_loss_summary.total_technical_opportunity_eur`, defined
in [`110_create_production_loss_views.sql`](../../sql/analytics/110_create_production_loss_views.sql).

## Sensitivity scenarios

The simple annualized technical-opportunity base is:

**€573,908,429.76 / 2 = €286,954,214.88 per year**

If a future implementation validated that only a small fraction of the modeled
annualized technical opportunity were economically recoverable, the
illustrative annual value would be:

| Realization rate | Illustrative annual value |
|---:|---:|
| 0.5% | €1,434,771.07 |
| 1.0% | €2,869,542.15 |
| 2.0% | €5,739,084.30 |
| 5.0% | €14,347,710.74 |

These scenarios are arithmetic sensitivity tests applied to a simple two-year
average. The annualized base is not a seasonality-adjusted estimate or forecast,
and none of these values is realized savings. The supporting scenario export is
[`annual_realization_sensitivity_2024_2025.csv`](../../data/gold/business_case/annual_realization_sensitivity_2024_2025.csv).

## Benefit categories

### Production / OEE

Potential mechanisms:
- quicker identification of chronic losses;
- line/site benchmarking;
- loss Pareto analysis;
- better prioritization of improvement work.

### Energy

Potential mechanisms:
- site and line intensity benchmarking;
- contextual energy anomaly detection;
- identification of avoidable high-energy operating periods.

Energy benefits should be calculated independently from production opportunity
to avoid double counting.

### Maintenance / Reliability

Potential mechanisms:
- failure and downtime Pareto;
- equipment burden ranking;
- reliability trend monitoring;
- condition-classification workflows where suitable telemetry exists.

The current portfolio's MTBF and availability metrics include explicitly
labelled proxies and should not be converted directly into financial savings
without site-specific validation.

### Quality

Potential mechanisms:
- reject-rate monitoring;
- statistically appropriate process-control monitoring;
- earlier investigation of abnormal quality behavior.

### Data / reporting productivity

Potential mechanisms:
- reduced manual data consolidation;
- standardized KPI definitions;
- repeatable data-quality checks;
- governed reporting model.

No labor-saving value is assigned in the portfolio because no validated
baseline effort/cost exists.

## Financial model

For a real implementation:

`Annual gross benefit = validated addressable opportunity × realized improvement rate`

`Annual net benefit = annual gross benefit - annual platform operating cost`

`ROI = (annual net benefit - annualized implementation cost) / annualized implementation cost`

`Payback months = implementation cost / monthly net benefit`

These calculations should only be populated after:

- deployment scope is confirmed;
- internal/external labor cost is known;
- software/cloud/licensing cost is known;
- baseline losses are validated;
- benefit ownership is assigned;
- realization assumptions are approved.

## Avoiding double counting

Do not automatically sum:

- production opportunity;
- quality benefit;
- energy benefit;
- maintenance benefit.

A single event may affect multiple domains. Financial realization must be tied
to a mutually exclusive benefit ledger or explicitly adjusted for overlap.

## Business-case decision criteria

Proceed from pilot to scaled implementation only when:

1. source data can be integrated reliably;
2. priority KPIs reconcile to authoritative systems;
3. users actively use the outputs for operating decisions;
4. at least one measurable improvement use case is validated;
5. expected recurring value exceeds recurring platform cost;
6. governance and security requirements are satisfied.

## Portfolio position

The project demonstrates the capability to build the platform and the method
for evaluating value.

It does not claim that Velora Beverage Group is a real organization or that the
modeled opportunity has been realized.
