# Stage 11B Power BI relationship map

## Model direction

Use a star-schema pattern with single-direction filtering from dimensions to facts.

Do not create fact-to-fact relationships.

## Dimensions

- `dim_time`
- `dim_site`
- `dim_line`
- `dim_product`
- `dim_shift`

## Gold facts

- `gold.vw_shift_manufacturing_performance`
- `gold.vw_line_daily_performance`
- `gold.vw_site_daily_performance`
- `gold.vw_site_executive_summary`
- `gold.vw_data_quality_domain_summary`
- `gold.vw_data_quality_rule_status`

## Relationships to create

### Date

`dim_time[date_id]` 1 -> * `gold.vw_shift_manufacturing_performance[date_id]`

`dim_time[date_id]` 1 -> * `gold.vw_line_daily_performance[date_id]`

`dim_time[date_id]` 1 -> * `gold.vw_site_daily_performance[date_id]`

Cross-filter direction: Single.

### Site

`dim_site[site_code]` 1 -> * `gold.vw_shift_manufacturing_performance[site_code]`

`dim_site[site_code]` 1 -> * `gold.vw_line_daily_performance[site_code]`

`dim_site[site_code]` 1 -> * `gold.vw_site_daily_performance[site_code]`

`dim_site[site_code]` 1 -> * `gold.vw_site_executive_summary[site_code]`

Cross-filter direction: Single.

### Line

`dim_line[line_code]` 1 -> * `gold.vw_shift_manufacturing_performance[line_code]`

`dim_line[line_code]` 1 -> * `gold.vw_line_daily_performance[line_code]`

Cross-filter direction: Single.

### Product

`dim_product[product_code]` 1 -> * `gold.vw_shift_manufacturing_performance[product_code]`

Cross-filter direction: Single.

### Shift

`dim_shift[shift_code]` 1 -> * `gold.vw_shift_manufacturing_performance[shift_code]`

Cross-filter direction: Single.

## DQ tables

Leave these two disconnected from the production star unless a later reporting requirement specifically needs a shared dimension:

- `gold.vw_data_quality_domain_summary`
- `gold.vw_data_quality_rule_status`

They form their own small reporting island.

## Site and line hierarchy

For report navigation, create this hierarchy in `dim_site` / `dim_line`:

Site:
- site_name
- country_code
- region

Line:
- line_name
- line_type

Do not force a direct relationship from `dim_site` to `dim_line` if both are already filtering the Gold facts independently by business key. Keeping both as dimensions avoids unnecessary ambiguity.

## Date settings

Mark `dim_time[calendar_date]` as the Date table date column.

Useful display columns:

- year
- quarter
- month
- month_name
- week_of_year
- day_name
- is_weekend

Sort `month_name` by `month`.

## Import mode

Use Import mode for all Stage 11 reporting tables.

This is appropriate because the current curated model is moderate in size and the project does not require live operational DirectQuery behaviour.
