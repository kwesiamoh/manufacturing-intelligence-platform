-- utilities — Supplemental utility/energy-detail tables.
-- These preserve energy and utilities fields not carried by the original fact_energy schema.

CREATE TABLE IF NOT EXISTS fact_line_energy_detail (
    line_energy_detail_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_dataset_id INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    energy_record_id VARCHAR(64) NOT NULL,
    production_record_id VARCHAR(64) NOT NULL,
    site_id INTEGER NOT NULL REFERENCES dim_site(site_id),
    line_id INTEGER NOT NULL REFERENCES dim_line(line_id),
    shift_id INTEGER NOT NULL REFERENCES dim_shift(shift_id),
    product_id INTEGER NOT NULL REFERENCES dim_product(product_id),
    timestamp_start TIMESTAMP NOT NULL,
    timestamp_end TIMESTAMP NOT NULL,
    actual_quantity BIGINT NOT NULL,
    line_production_electricity_kwh NUMERIC NOT NULL,
    line_idle_electricity_kwh NUMERIC NOT NULL,
    line_total_electricity_kwh NUMERIC NOT NULL,
    compressed_air_nm3 NUMERIC,
    compressed_air_nm3_per_1000_units NUMERIC,
    shift_mean_air_temperature_c NUMERIC,
    site_auxiliary_base_kw NUMERIC,
    site_weather_auxiliary_kw NUMERIC,
    data_class VARCHAR(64),
    integration_role VARCHAR(64),
    weather_data_class VARCHAR(64),
    generator_seed INTEGER,
    UNIQUE (source_dataset_id, energy_record_id)
);

CREATE TABLE IF NOT EXISTS fact_site_energy_detail (
    site_energy_detail_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_dataset_id INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    site_energy_record_id VARCHAR(96) NOT NULL,
    site_id INTEGER NOT NULL REFERENCES dim_site(site_id),
    shift_id INTEGER NOT NULL REFERENCES dim_shift(shift_id),
    timestamp_start TIMESTAMP NOT NULL,
    timestamp_end TIMESTAMP NOT NULL,
    line_electricity_kwh NUMERIC NOT NULL,
    production_units BIGINT NOT NULL,
    mean_air_temperature_c NUMERIC,
    site_auxiliary_base_kw NUMERIC NOT NULL,
    site_weather_auxiliary_kw NUMERIC NOT NULL,
    shift_hours NUMERIC NOT NULL,
    site_auxiliary_electricity_kwh NUMERIC NOT NULL,
    site_total_electricity_kwh NUMERIC NOT NULL,
    site_energy_intensity_kwh_per_1000_units NUMERIC NOT NULL,
    data_class VARCHAR(64),
    integration_role VARCHAR(64),
    weather_data_class VARCHAR(64),
    UNIQUE (source_dataset_id, site_energy_record_id)
);

CREATE INDEX IF NOT EXISTS idx_line_energy_detail_site_line_time
    ON fact_line_energy_detail(site_id, line_id, timestamp_start);

CREATE INDEX IF NOT EXISTS idx_site_energy_detail_site_time
    ON fact_site_energy_detail(site_id, timestamp_start);
