# Stage 5B loss-accounting fields

| Field | Meaning |
|---|---|
| theoretical_capacity_units | Output possible during planned production time at nominal rate |
| operating_capacity_units | Output possible during actual operating time at nominal rate |
| availability_loss_units | Technical units lost because the line was not operating |
| planned_downtime_loss_units_exact | Availability loss attributable to planned downtime |
| unplanned_downtime_loss_units_exact | Availability loss attributable to unplanned downtime |
| changeover_loss_units_subset | Planned-downtime loss attributable specifically to changeover; subset only |
| performance_loss_units | Technical units lost because actual running speed was below nominal |
| quality_loss_units | Produced units rejected as non-good output |
| total_technical_loss_units | Availability + performance + quality loss |
| technical_capacity_gap_units | Theoretical capacity units minus good units |
| plan_shortfall_units | Positive shortfall of good output versus production plan |
| standard_loss_value_eur_per_unit | Synthetic internal unit opportunity-value assumption |
| total_technical_opportunity_eur | Technical loss units translated by product standard unit value |
| plan_shortfall_opportunity_eur | Plan shortfall translated by product standard unit value |
