# Interpretation notes

MECS is aggregate survey data, not equipment-level telemetry.

EIA reports manufacturing estimates by NAICS industry and region. Workbooks may include suppression
symbols, footnotes, units and multi-row headers. Preserve those until the formal schema-mapping step.

Valid benchmark uses:
- manufacturing natural-gas consumption;
- purchased-steam quantities and prices;
- purchased-energy expenditure;
- industry fuel-mix comparisons;
- industry/region energy-economic comparisons.

Invalid direct uses:
- hourly site gas demand;
- steam demand for an individual production line;
- product-level fuel intensity;
- fictional-site exact utility bills.

Those require a genuine plant-level source or an explicitly documented synthetic integration layer.
