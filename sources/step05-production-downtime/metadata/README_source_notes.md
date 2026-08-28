# Source notes

The source should be treated as a measured single-line industrial dataset, not as evidence of a six-site enterprise.

What it can support directly:

- production quantity over time
- daily/hourly operating time
- downtime duration
- event timestamps
- measured operating efficiency from the source
- product-size context (3 L / 5 L where populated)
- production forecasting experiments

What it does **not** support directly:

- six-site hierarchy
- 30 production lines
- downtime root causes
- detailed asset IDs
- maintenance work orders
- quality defects/scrap causes
- cost/contribution margin
- corporate targets
- complete OEE Availability × Performance × Quality decomposition

Those gaps will be filled only from additional real datasets where possible. Synthetic integration fields, if ultimately required, will be explicitly identified as synthetic rather than presented as measured source data.
