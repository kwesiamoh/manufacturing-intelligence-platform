# Canonical Dimensions

## dim_source_dataset
Grain: one record per external/public dataset.

- source_dataset_id — INTEGER PK
- source_code — VARCHAR
- source_name — VARCHAR
- publisher — VARCHAR
- source_domain — VARCHAR
- integration_role — VARCHAR
- is_real_data — BOOLEAN
- source_url — VARCHAR
- license — VARCHAR NULL
- reference_period — VARCHAR NULL
- notes — TEXT NULL

## dim_site
Grain: one manufacturing or source facility/site.

- site_id — INTEGER PK
- site_code — VARCHAR
- site_name — VARCHAR
- country_code — VARCHAR NULL
- region — VARCHAR NULL
- site_type — VARCHAR NULL
- source_dataset_id — INTEGER FK NULL
- site_origin — VARCHAR
- active_flag — BOOLEAN

## dim_area
Grain: one production/support area within a site.

- area_id — INTEGER PK
- site_id — INTEGER FK
- area_code — VARCHAR
- area_name — VARCHAR
- area_type — VARCHAR

## dim_line
Grain: one production line.

- line_id — INTEGER PK
- site_id — INTEGER FK
- area_id — INTEGER FK
- line_code — VARCHAR
- line_name — VARCHAR
- line_type — VARCHAR NULL
- nominal_capacity — NUMERIC NULL
- capacity_unit — VARCHAR NULL
- commissioning_year — INTEGER NULL
- source_dataset_id — INTEGER FK NULL
- active_flag — BOOLEAN

## dim_equipment
Grain: one physical asset.

- equipment_id — INTEGER PK
- line_id — INTEGER FK NULL
- area_id — INTEGER FK NULL
- equipment_code — VARCHAR
- equipment_name — VARCHAR
- equipment_type — VARCHAR
- criticality_class — VARCHAR NULL
- commissioning_date — DATE NULL
- rated_power_kw — NUMERIC NULL
- source_dataset_id — INTEGER FK
- active_flag — BOOLEAN

## dim_sensor
Grain: one telemetry tag/sensor.

- sensor_id — INTEGER PK
- equipment_id — INTEGER FK
- sensor_code — VARCHAR
- sensor_name — VARCHAR
- measurement_type — VARCHAR
- engineering_unit — VARCHAR NULL
- sampling_interval_seconds — NUMERIC NULL
- source_dataset_id — INTEGER FK
- active_flag — BOOLEAN

## dim_product
Grain: one product/SKU/product class.

- product_id — INTEGER PK
- product_code — VARCHAR
- product_name — VARCHAR
- product_family — VARCHAR NULL
- package_type — VARCHAR NULL
- package_size — NUMERIC NULL
- package_unit — VARCHAR NULL
- source_dataset_id — INTEGER FK NULL

## dim_shift
Grain: one defined shift pattern.

- shift_id — INTEGER PK
- shift_code — VARCHAR
- shift_name — VARCHAR
- start_time — TIME
- end_time — TIME
- crosses_midnight — BOOLEAN

## dim_failure_reason
Grain: one standardized downtime/failure classification.

- failure_reason_id — INTEGER PK
- failure_category — VARCHAR
- failure_reason — VARCHAR
- planned_flag — BOOLEAN
- source_reason_code — VARCHAR NULL
- source_dataset_id — INTEGER FK NULL

## dim_utility
Grain: one utility type.

- utility_id — INTEGER PK
- utility_code — VARCHAR
- utility_name — VARCHAR
- default_unit — VARCHAR NULL
- utility_category — VARCHAR

Initial utility codes:
- ELECTRICITY
- NATURAL_GAS
- STEAM
- COMPRESSED_AIR
- PROCESS_WATER
- COOLING_WATER
- CHILLED_WATER

## dim_time
Grain: one calendar date.

- date_id — INTEGER PK
- calendar_date — DATE
- year — INTEGER
- quarter — INTEGER
- month — INTEGER
- month_name — VARCHAR
- week_of_year — INTEGER
- day_of_month — INTEGER
- day_of_week — INTEGER
- day_name — VARCHAR
- is_weekend — BOOLEAN
