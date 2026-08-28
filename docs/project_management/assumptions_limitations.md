# Assumptions and Limitations

## Enterprise data

The six-site beverage enterprise is synthetic.

It is used to demonstrate enterprise data integration, KPI modelling, Power BI,
and analytical workflows.

## Real external sources

Real datasets are used where available, including telemetry and hydraulic
condition monitoring.

They are not represented as originating from the fictional beverage enterprise.

## Advanced analytics

### SPC
Laney p-prime is the accepted final quality-control method. The original
ordinary p-chart remains diagnostic evidence of overdispersion.

### Telemetry anomalies
MetroPT anomaly detection is presented as anomaly/fault-event detection. It is
not claimed as a reliable two-hour predictive-maintenance warning system.

### Energy anomaly analytics
The energy model uses synthetic enterprise data and demonstrates contextual
anomaly detection.

### Forecasting
Forecasting is one-day-ahead rolling operational forecasting. It is not a
single-origin 60-day recursive forecast.

### Reliability
Operating-hours MTBF and availability are explicitly proxies because direct
runtime is not available for each equipment asset.

### Hydraulic condition monitoring
The real benchmark supports condition classification. It is not used to claim
remaining useful life or future-failure forecasting.

## Cloud

AWS is target architecture only. No live AWS environment is claimed.

## Portfolio scope

The project is designed to demonstrate an end-to-end manufacturing intelligence
platform, not to exhaustively optimize every analytical model or simulate every
possible enterprise control.
