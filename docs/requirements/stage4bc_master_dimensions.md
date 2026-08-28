# Stage 4B/4C — Master Dimension Loading

## Purpose
Load the canonical PostgreSQL dimensions needed before fact loading.

## Loaded now
- source datasets
- fictional beverage sites
- production and utility areas
- production lines
- beverage products
- three shifts
- beverage equipment hierarchy
- downtime/failure reasons
- static utilities
- calendar time

## Intentionally empty
`dim_sensor` remains empty because the fictional enterprise does not yet have a synthetic sensor/tag master. Real telemetry sources will be handled separately and must retain their own source identities.

## Area model
Only two areas per fictional site are created:
- Production
- Utilities

This is sufficient for the current scope and avoids unnecessary plant-area hierarchy detail.

## Calendar
`dim_time` spans 2005-01-01 through 2026-12-31 so the enterprise data and the main historical benchmark datasets can share one reporting calendar.

## Scope boundary
No fact rows are loaded in this step.
