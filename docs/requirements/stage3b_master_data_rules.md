# Stage 3B Enterprise Master Data Rules

## Scope
Stage 3B defines only:
- one fictional beverage company
- six already-fixed sites
- 30 production lines
- six beverage products
- product-to-line compatibility
- one three-shift pattern
- nominal line capacities

No production history, OEE, downtime events, maintenance work orders, quality events, energy consumption, or financial-loss records are generated here.

## Line design
Each site has five lines:
1. one still-water PET line
2. two flexible carbonated PET lines
3. one additional carbonated soft-drink PET line
4. one specialty line for either juice or energy drinks

Germany, Poland, and Spain receive energy-drink can lines.
Netherlands, Czechia, and France receive 1 L juice lines.

This gives common products across all six sites for cross-site benchmarking while retaining some site specialization.

## Capacity rule
Nominal capacities are synthetic master data, not claims about real plants.

They are fixed by line class rather than randomized:
- PET still water: 43,200 bottles/hour
- PET carbonated beverages: 40,000 bottles/hour
- 1 L juice: 27,000 bottles/hour
- 250 mL cans: 60,000 cans/hour

The first three values are anchored directly to published commercial examples. The can value is a conservative synthetic design point inside Krones' published 18,000-135,000 cans/hour range.

## Shift rule
One common three-shift pattern is used across the enterprise:
- Shift A: 06:00-14:00
- Shift B: 14:00-22:00
- Shift C: 22:00-06:00

Detailed calendars, planned downtime, breaks, and production schedules are deferred to the production-plan generation step.

## Data classification
All entities in this package are explicitly synthetic master data or synthetic mappings. Real public datasets retain their original provenance.
