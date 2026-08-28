# Canonical Facts

## fact_telemetry
Grain: one sensor measurement at one timestamp.
- telemetry_id
- timestamp
- sensor_id
- equipment_id
- source_dataset_id
- measurement_value
- engineering_unit
- quality_flag

## fact_production
Grain: production performance for one line/product/time interval.
- production_id
- timestamp_start
- timestamp_end
- date_id
- site_id
- line_id
- product_id
- shift_id
- source_dataset_id
- planned_quantity
- actual_quantity
- good_quantity
- reject_quantity
- nominal_rate
- actual_rate
- operating_time_min
- planned_production_time_min

## fact_downtime
Grain: one downtime event.
- downtime_id
- event_start
- event_end
- date_id
- site_id
- line_id
- equipment_id
- shift_id
- failure_reason_id
- source_dataset_id
- duration_min
- planned_flag
- production_loss_quantity
- source_event_code

## fact_quality
Grain: one quality observation, inspection result, or production-quality summary.
- quality_id
- timestamp
- date_id
- site_id
- line_id
- equipment_id
- product_id
- source_dataset_id
- total_quantity
- good_quantity
- reject_quantity
- rework_quantity
- quality_result
- defect_code
- measurement_value
- lower_spec_limit
- upper_spec_limit

## fact_maintenance
Grain: one maintenance work order or intervention.
- maintenance_id
- site_id
- equipment_id
- source_dataset_id
- work_order_id
- maintenance_type
- failure_reason_id
- start_timestamp
- end_timestamp
- duration_hours
- labor_hours
- labor_cost
- material_cost
- other_cost
- total_cost
- planned_flag

## fact_energy
Grain: one energy observation for a defined period/entity.
- energy_id
- timestamp
- date_id
- site_id
- area_id
- line_id
- equipment_id
- utility_id
- source_dataset_id
- consumption
- demand
- energy_cost
- measurement_unit

## fact_utility
Grain: one utility measurement.
- utility_measurement_id
- timestamp
- site_id
- area_id
- line_id
- equipment_id
- utility_id
- source_dataset_id
- measurement_type
- measurement_value
- engineering_unit

## fact_water
Grain: one water-use observation or benchmark record.
- water_id
- date_id
- site_id
- source_dataset_id
- water_use_category
- industry_code
- volume
- volume_unit
- data_quality_status

## fact_emissions
Grain: one installation/activity/year emissions record.
- emissions_id
- date_id
- site_id
- source_dataset_id
- installation_id
- activity_code
- verified_emissions
- emissions_unit
- country_code

## fact_energy_price
Grain: one energy price by country, period, commodity, and consumption band.
- energy_price_id
- date_id
- source_dataset_id
- country_code
- utility_id
- consumption_band
- price
- currency
- price_unit
- tax_treatment

## fact_production_order
Grain: one production order/campaign/session.
- production_order_id
- site_id
- line_id
- product_id
- source_dataset_id
- order_code
- planned_start
- planned_end
- actual_start
- actual_end
- planned_quantity
- actual_quantity
- changeover_duration_min
- production_status

## fact_weather_context
Grain: one weather observation for one site/grid point/time.
- weather_id
- timestamp
- site_id
- source_dataset_id
- air_temperature
- dewpoint_temperature
- surface_pressure
- wind_speed
- solar_radiation
- precipitation

## fact_data_quality
Grain: one detected data-quality issue.
- data_quality_id
- detected_timestamp
- source_dataset_id
- site_id
- line_id
- equipment_id
- sensor_id
- issue_type
- severity
- affected_records
- issue_start
- issue_end
- status
