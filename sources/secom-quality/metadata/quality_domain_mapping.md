# Domain mapping

This dataset is used only for the platform's process and quality domain.

- `secom.data`: anonymous real-valued manufacturing process/sensor measurements.
- `secom_labels.data`: pass/fail yield class and timestamp.
- `secom.names`: original dataset documentation.

Anonymous sensors are not renamed as specific physical variables because doing
so would invent semantics not supplied by UCI.

Silver output fields added by the pipeline are limited to integration-safe fields such as `sample_id`, `event_timestamp`, `raw_label`, and `quality_result`, plus anonymous `sensor_###` columns.
