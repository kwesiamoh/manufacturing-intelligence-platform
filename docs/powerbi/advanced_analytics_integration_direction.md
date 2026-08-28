# Integration Direction

Accepted Velora-facing analytics:

1. Stage 12E production forecast
2. Stage 12E energy forecast
3. Stage 12D contextual energy anomaly analytics
4. Stage 13D.2 reliability trends

External benchmark analytics remain separate:

- MetroPT fault/anomaly detection
- Hydraulic condition classification

These external datasets may be documented in the portfolio, but should not be
shown as Velora plant operational predictions.

Target flow:

`Python analytics -> accepted output tables -> PostgreSQL analytics/gold_bi -> Power BI`

Power BI should consume model outputs; it should not retrain the Python models.
