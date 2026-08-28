-- Manufacturing Intelligence Platform
-- Stage 2D: Canonical facts
-- PostgreSQL

CREATE TABLE IF NOT EXISTS fact_telemetry (
    telemetry_id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    timestamp              TIMESTAMP NOT NULL,
    sensor_id              INTEGER NOT NULL REFERENCES dim_sensor(sensor_id),
    equipment_id           INTEGER NOT NULL REFERENCES dim_equipment(equipment_id),
    source_dataset_id      INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    measurement_value      DOUBLE PRECISION,
    engineering_unit       VARCHAR(50),
    quality_flag           VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS fact_production (
    production_id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    timestamp_start                TIMESTAMP NOT NULL,
    timestamp_end                  TIMESTAMP,
    date_id                        INTEGER NOT NULL REFERENCES dim_time(date_id),
    site_id                        INTEGER REFERENCES dim_site(site_id),
    line_id                        INTEGER REFERENCES dim_line(line_id),
    product_id                     INTEGER REFERENCES dim_product(product_id),
    shift_id                       INTEGER REFERENCES dim_shift(shift_id),
    source_dataset_id              INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    planned_quantity               NUMERIC,
    actual_quantity                NUMERIC,
    good_quantity                  NUMERIC,
    reject_quantity                NUMERIC,
    nominal_rate                   NUMERIC,
    actual_rate                    NUMERIC,
    operating_time_min             NUMERIC,
    planned_production_time_min    NUMERIC
);

CREATE TABLE IF NOT EXISTS fact_downtime (
    downtime_id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_start              TIMESTAMP NOT NULL,
    event_end                TIMESTAMP,
    date_id                  INTEGER NOT NULL REFERENCES dim_time(date_id),
    site_id                  INTEGER REFERENCES dim_site(site_id),
    line_id                  INTEGER REFERENCES dim_line(line_id),
    equipment_id             INTEGER REFERENCES dim_equipment(equipment_id),
    shift_id                 INTEGER REFERENCES dim_shift(shift_id),
    failure_reason_id        INTEGER REFERENCES dim_failure_reason(failure_reason_id),
    source_dataset_id        INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    duration_min             NUMERIC,
    planned_flag             BOOLEAN,
    production_loss_quantity NUMERIC,
    source_event_code        VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS fact_quality (
    quality_id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    timestamp               TIMESTAMP,
    date_id                 INTEGER REFERENCES dim_time(date_id),
    site_id                 INTEGER REFERENCES dim_site(site_id),
    line_id                 INTEGER REFERENCES dim_line(line_id),
    equipment_id            INTEGER REFERENCES dim_equipment(equipment_id),
    product_id              INTEGER REFERENCES dim_product(product_id),
    source_dataset_id       INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    total_quantity          NUMERIC,
    good_quantity           NUMERIC,
    reject_quantity         NUMERIC,
    rework_quantity         NUMERIC,
    quality_result          VARCHAR(50),
    defect_code             VARCHAR(100),
    measurement_value       DOUBLE PRECISION,
    lower_spec_limit        DOUBLE PRECISION,
    upper_spec_limit        DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS fact_maintenance (
    maintenance_id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    site_id                 INTEGER REFERENCES dim_site(site_id),
    equipment_id            INTEGER REFERENCES dim_equipment(equipment_id),
    source_dataset_id       INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    work_order_id           VARCHAR(120),
    maintenance_type        VARCHAR(100),
    failure_reason_id       INTEGER REFERENCES dim_failure_reason(failure_reason_id),
    start_timestamp         TIMESTAMP,
    end_timestamp           TIMESTAMP,
    duration_hours          NUMERIC,
    labor_hours             NUMERIC,
    labor_cost              NUMERIC,
    material_cost           NUMERIC,
    other_cost              NUMERIC,
    total_cost              NUMERIC,
    planned_flag            BOOLEAN
);

CREATE TABLE IF NOT EXISTS fact_energy (
    energy_id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    timestamp               TIMESTAMP,
    date_id                 INTEGER REFERENCES dim_time(date_id),
    site_id                 INTEGER REFERENCES dim_site(site_id),
    area_id                 INTEGER REFERENCES dim_area(area_id),
    line_id                 INTEGER REFERENCES dim_line(line_id),
    equipment_id            INTEGER REFERENCES dim_equipment(equipment_id),
    utility_id              INTEGER NOT NULL REFERENCES dim_utility(utility_id),
    source_dataset_id       INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    consumption             NUMERIC,
    demand                  NUMERIC,
    energy_cost             NUMERIC,
    measurement_unit        VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS fact_utility (
    utility_measurement_id  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    timestamp               TIMESTAMP,
    site_id                 INTEGER REFERENCES dim_site(site_id),
    area_id                 INTEGER REFERENCES dim_area(area_id),
    line_id                 INTEGER REFERENCES dim_line(line_id),
    equipment_id            INTEGER REFERENCES dim_equipment(equipment_id),
    utility_id              INTEGER NOT NULL REFERENCES dim_utility(utility_id),
    source_dataset_id       INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    measurement_type        VARCHAR(100) NOT NULL,
    measurement_value       DOUBLE PRECISION,
    engineering_unit        VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS fact_water (
    water_id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    date_id                 INTEGER REFERENCES dim_time(date_id),
    site_id                 INTEGER REFERENCES dim_site(site_id),
    source_dataset_id       INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    water_use_category      VARCHAR(120),
    industry_code           VARCHAR(100),
    volume                  NUMERIC,
    volume_unit             VARCHAR(50),
    data_quality_status     VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS fact_emissions (
    emissions_id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    date_id                 INTEGER REFERENCES dim_time(date_id),
    site_id                 INTEGER REFERENCES dim_site(site_id),
    source_dataset_id       INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    installation_id         VARCHAR(120),
    activity_code           VARCHAR(100),
    verified_emissions      NUMERIC,
    emissions_unit          VARCHAR(50),
    country_code            VARCHAR(3)
);

CREATE TABLE IF NOT EXISTS fact_energy_price (
    energy_price_id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    date_id                 INTEGER REFERENCES dim_time(date_id),
    source_dataset_id       INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    country_code            VARCHAR(3) NOT NULL,
    utility_id              INTEGER NOT NULL REFERENCES dim_utility(utility_id),
    consumption_band        VARCHAR(100),
    price                   NUMERIC,
    currency                VARCHAR(10),
    price_unit              VARCHAR(50),
    tax_treatment           VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS fact_production_order (
    production_order_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    site_id                 INTEGER REFERENCES dim_site(site_id),
    line_id                 INTEGER REFERENCES dim_line(line_id),
    product_id              INTEGER REFERENCES dim_product(product_id),
    source_dataset_id       INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    order_code              VARCHAR(120),
    planned_start           TIMESTAMP,
    planned_end             TIMESTAMP,
    actual_start            TIMESTAMP,
    actual_end              TIMESTAMP,
    planned_quantity        NUMERIC,
    actual_quantity         NUMERIC,
    changeover_duration_min NUMERIC,
    production_status       VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS fact_weather_context (
    weather_id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    timestamp               TIMESTAMP NOT NULL,
    site_id                 INTEGER NOT NULL REFERENCES dim_site(site_id),
    source_dataset_id       INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    air_temperature         DOUBLE PRECISION,
    dewpoint_temperature    DOUBLE PRECISION,
    surface_pressure        DOUBLE PRECISION,
    wind_speed              DOUBLE PRECISION,
    solar_radiation         DOUBLE PRECISION,
    precipitation           DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS fact_data_quality (
    data_quality_id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    detected_timestamp      TIMESTAMP NOT NULL,
    source_dataset_id       INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    site_id                 INTEGER REFERENCES dim_site(site_id),
    line_id                 INTEGER REFERENCES dim_line(line_id),
    equipment_id            INTEGER REFERENCES dim_equipment(equipment_id),
    sensor_id               INTEGER REFERENCES dim_sensor(sensor_id),
    issue_type              VARCHAR(100) NOT NULL,
    severity                VARCHAR(40),
    affected_records        BIGINT,
    issue_start             TIMESTAMP,
    issue_end               TIMESTAMP,
    status                  VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_fact_telemetry_timestamp
    ON fact_telemetry(timestamp);

CREATE INDEX IF NOT EXISTS idx_fact_telemetry_sensor_timestamp
    ON fact_telemetry(sensor_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_fact_production_date_line
    ON fact_production(date_id, line_id);

CREATE INDEX IF NOT EXISTS idx_fact_downtime_start_line
    ON fact_downtime(event_start, line_id);

CREATE INDEX IF NOT EXISTS idx_fact_maintenance_equipment
    ON fact_maintenance(equipment_id);

CREATE INDEX IF NOT EXISTS idx_fact_energy_date_site
    ON fact_energy(date_id, site_id);

CREATE INDEX IF NOT EXISTS idx_fact_utility_timestamp
    ON fact_utility(timestamp);
