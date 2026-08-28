# Domain mapping

This dataset is used only for the process/quality domain of the portfolio platform.

- `secom.data`: anonymous real-valued manufacturing process/sensor measurements.
- `secom_labels.data`: pass/fail yield class and timestamp.
- `secom.names`: original dataset documentation.

No attempt is made at this stage to rename anonymous sensors as specific physical variables. Doing so would invent semantics not supplied by UCI.

Silver output fields added by the pipeline are limited to integration-safe fields such as `sample_id`, `event_timestamp`, `raw_label`, and `quality_result`, plus anonymous `sensor_###` columns.
