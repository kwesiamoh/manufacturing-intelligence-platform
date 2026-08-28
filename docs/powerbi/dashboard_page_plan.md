# Power BI report structure

## Page 1 - Executive overview
Primary source: `gold.vw_site_executive_summary`

Top KPIs:
- OEE
- production attainment
- total technical opportunity EUR
- total-site energy intensity
- benchmark electricity cost per 1,000 units
- DQ status

Core visuals:
- site OEE ranking
- technical opportunity by site
- energy-intensity comparison
- benchmark electricity-cost comparison

## Page 2 - Production performance
Primary sources:
- `gold.vw_line_daily_performance`
- `gold.vw_shift_manufacturing_performance`

Core visuals:
- OEE trend
- availability / performance / quality
- production attainment
- throughput
- reject rate
- line ranking

## Page 3 - Loss and opportunity
Primary sources:
- `gold.vw_shift_manufacturing_performance`
- `gold.vw_line_daily_performance`

Core visuals:
- availability / performance / quality loss split
- planned vs unplanned downtime opportunity
- changeover opportunity
- technical opportunity trend
- downtime Pareto using the existing detailed analytical view if required

## Page 4 - Energy and utilities
Primary sources:
- `gold.vw_shift_manufacturing_performance`
- `gold.vw_site_daily_performance`
- `gold.vw_site_executive_summary`

Core visuals:
- kWh per 1,000 good units
- total-site kWh per 1,000 units
- idle-energy share
- auxiliary-energy share
- compressed-air intensity
- site benchmark electricity cost
- weather / auxiliary-load context

## Page 5 - Data quality
Primary sources:
- `gold.vw_data_quality_domain_summary`
- `gold.vw_data_quality_rule_status`

Core visuals:
- enterprise/domain DQ score
- PASS/WARN/FAIL rule counts
- rule detail table
- telemetry warning categories
