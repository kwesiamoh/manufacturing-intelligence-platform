# Stage 11A Power BI semantic model

## Goal

Stage 11A establishes the Power BI semantic model and PostgreSQL connection.

Business logic already validated in PostgreSQL remains in SQL. Power BI is used for filtering, presentation measures, comparisons and dashboard interaction.

## Connection

Use Power BI Desktop and connect with the PostgreSQL connector.

Server:

`localhost:5433`

Database:

`manufacturing_intelligence`

Use **Import** mode for this portfolio project.

Import mode is preferred here because the curated Gold dataset is moderate in size, dashboard interaction will be fast, and the project does not require live operational DirectQuery behavior.

## Reporting tables

Load these Gold views:

- `gold.vw_shift_manufacturing_performance`
- `gold.vw_line_daily_performance`
- `gold.vw_site_daily_performance`
- `gold.vw_site_executive_summary`
- `gold.vw_data_quality_domain_summary`
- `gold.vw_data_quality_rule_status`

Load these dimensions from `public`:

- `dim_site`
- `dim_line`
- `dim_product`
- `dim_shift`
- `dim_time`

Do not load every Stage 5, Stage 6 and Stage 7 analytical view into Power BI. They remain available for specialist drill-through if needed, but the Gold layer is the normal reporting interface.

## Intended star-schema relationships

The final relationships will use the business keys already present in the Gold models:

- Date dimension -> Gold daily/shift facts through `date_id`
- Site dimension -> Gold facts through `site_code`
- Line dimension -> line/shift Gold facts through `line_code`
- Product dimension -> shift Gold fact through `product_code`
- Shift dimension -> shift Gold fact through `shift_code`

Relationships should normally be:

- one-to-many
- dimension to fact
- single-direction filtering

Avoid fact-to-fact relationships.

The Stage 11A inventory script confirms the exact dimension columns and key uniqueness before we lock these relationships.

## Gold model roles

### Shift manufacturing performance
Detailed operational analysis and drill-down by site, line, product and shift.

### Line daily performance
Daily line trends, OEE, loss and energy comparison.

### Site daily performance
Site-level production, energy and opportunity trends.

### Site executive summary
One-row-per-site executive comparison. Best source for the executive overview page.

### Data-quality domain summary
DQ performance by domain.

### Data-quality rule status
Rule-level PASS/WARN/FAIL drill-down.

## Planned dashboard pages

1. Executive overview
2. Production performance
3. Loss and opportunity
4. Energy and utilities
5. Data quality

## Important modelling rules

- Do not recalculate validated SQL KPIs in DAX unless a user-selected time context requires aggregation.
- Do not sum ratios such as OEE, availability, performance, quality or intensity.
- Use weighted or recomputed measures where a period-level KPI is needed.
- Keep synthetic financial opportunity clearly labelled as an estimate.
- Keep Eurostat electricity cost clearly labelled as a benchmark estimate, not an invoice.
- Preserve telemetry WARN findings as warnings rather than failures.

## Stage 11A run

Before finalizing Power BI relationships, run:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
  -h localhost -p 5433 -U postgres `
  -d manufacturing_intelligence `
  -f .\sql\validation\500_inventory_powerbi_dimensions.sql
```

Send the output back. Stage 11B will then provide the exact relationship map and first DAX measure set.
