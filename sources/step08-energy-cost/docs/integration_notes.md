# Integration notes

This source is intentionally kept separate from the operational time-series sources.

## Why
The ITAC database is a real, large industrial energy-assessment database. It is valuable for financial
and energy-efficiency benchmarking, but the assessed plants are not the same physical facilities as the
other public datasets in this portfolio.

## Valid uses
- Analyze distributions of project cost, savings and payback.
- Compare implementation rates by recommendation class or industry.
- Build benchmark ranges for potential financial opportunity.
- Calibrate later synthetic financial fields only if the synthetic layer is explicitly documented.
- Support an enterprise Gold mart such as `gold_energy_opportunity_benchmark`.

## Invalid uses
- Do not assign an ITAC assessment directly to DE01, NL01, or any fictional site.
- Do not claim an ITAC recommendation occurred on the real beverage bottling line.
- Do not use recommendation savings as measured production losses.
- Do not infer missing utility-meter time series from annual assessment values.

## Suggested Gold outputs later
- recommendation_implementation_rate
- median_project_cost_by_category
- median_annual_savings_by_category
- median_payback_by_category
- energy_saving_opportunity_by_industry
