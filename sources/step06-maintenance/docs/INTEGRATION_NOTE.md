# Integration note

FMUCD is intentionally isolated from manufacturing operational facts.

Allowed uses:
- Generic CMMS/work-order dimensional modelling.
- Large-volume Bronze/Silver ingestion demonstrations.
- Cost and labour distribution benchmarking.
- Data-quality testing for heterogeneous CMMS records.
- Calibration evidence for a future synthetic manufacturing maintenance layer.

Not allowed:
- Replacing `UniversityID` with fictional plant IDs and claiming the records are manufacturing data.
- Joining these work orders to bottling-line telemetry, production or downtime by invented keys.
- Treating building systems/components as production-line equipment.
- Using source maintenance costs as direct beverage-plant financial losses without explicit modelling and adjustment.

A manufacturing-specific synthetic maintenance table, if later required, must be separately labelled `synthetic` and generated from documented assumptions/calibration rules.
