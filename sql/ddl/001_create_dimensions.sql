-- Manufacturing Intelligence Platform
-- canonical data model: Canonical dimensions
-- PostgreSQL

CREATE TABLE IF NOT EXISTS dim_source_dataset (
    source_dataset_id      INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_code            VARCHAR(64) NOT NULL UNIQUE,
    source_name            VARCHAR(255) NOT NULL,
    publisher              VARCHAR(255),
    source_domain          VARCHAR(100) NOT NULL,
    integration_role       VARCHAR(40) NOT NULL
        CHECK (integration_role IN ('OPERATIONAL','BENCHMARK','EXTERNAL_CONTEXT','REFERENCE','SYNTHETIC_INTEGRATION')),
    is_real_data           BOOLEAN NOT NULL DEFAULT TRUE,
    source_url             TEXT,
    license                VARCHAR(100),
    reference_period       VARCHAR(100),
    notes                  TEXT
);

CREATE TABLE IF NOT EXISTS dim_site (
    site_id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    site_code              VARCHAR(64) NOT NULL UNIQUE,
    site_name              VARCHAR(255) NOT NULL,
    country_code           VARCHAR(3),
    region                 VARCHAR(255),
    site_type              VARCHAR(100),
    source_dataset_id      INTEGER REFERENCES dim_source_dataset(source_dataset_id),
    site_origin            VARCHAR(40) NOT NULL
        CHECK (site_origin IN ('REAL_SOURCE','FICTIONAL_ENTERPRISE')),
    active_flag            BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS dim_area (
    area_id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    site_id                INTEGER NOT NULL REFERENCES dim_site(site_id),
    area_code              VARCHAR(64) NOT NULL,
    area_name              VARCHAR(255) NOT NULL,
    area_type              VARCHAR(100),
    UNIQUE (site_id, area_code)
);

CREATE TABLE IF NOT EXISTS dim_line (
    line_id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    site_id                INTEGER NOT NULL REFERENCES dim_site(site_id),
    area_id                INTEGER NOT NULL REFERENCES dim_area(area_id),
    line_code              VARCHAR(64) NOT NULL,
    line_name              VARCHAR(255) NOT NULL,
    line_type              VARCHAR(100),
    nominal_capacity       NUMERIC,
    capacity_unit          VARCHAR(50),
    commissioning_year     INTEGER,
    source_dataset_id      INTEGER REFERENCES dim_source_dataset(source_dataset_id),
    active_flag            BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (site_id, line_code)
);

CREATE TABLE IF NOT EXISTS dim_equipment (
    equipment_id           INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    line_id                INTEGER REFERENCES dim_line(line_id),
    area_id                INTEGER REFERENCES dim_area(area_id),
    equipment_code         VARCHAR(100) NOT NULL,
    equipment_name         VARCHAR(255) NOT NULL,
    equipment_type         VARCHAR(120) NOT NULL,
    criticality_class      VARCHAR(20),
    commissioning_date     DATE,
    rated_power_kw         NUMERIC,
    source_dataset_id      INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    active_flag            BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (source_dataset_id, equipment_code)
);

CREATE TABLE IF NOT EXISTS dim_sensor (
    sensor_id                  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    equipment_id               INTEGER NOT NULL REFERENCES dim_equipment(equipment_id),
    sensor_code                VARCHAR(100) NOT NULL,
    sensor_name                VARCHAR(255) NOT NULL,
    measurement_type           VARCHAR(120) NOT NULL,
    engineering_unit           VARCHAR(50),
    sampling_interval_seconds  NUMERIC,
    source_dataset_id          INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    active_flag                BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (source_dataset_id, sensor_code)
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_id             INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_code           VARCHAR(100) NOT NULL,
    product_name           VARCHAR(255) NOT NULL,
    product_family         VARCHAR(120),
    package_type           VARCHAR(100),
    package_size           NUMERIC,
    package_unit           VARCHAR(50),
    source_dataset_id      INTEGER REFERENCES dim_source_dataset(source_dataset_id),
    UNIQUE (source_dataset_id, product_code)
);

CREATE TABLE IF NOT EXISTS dim_shift (
    shift_id               INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shift_code             VARCHAR(50) NOT NULL UNIQUE,
    shift_name             VARCHAR(100) NOT NULL,
    start_time             TIME NOT NULL,
    end_time               TIME NOT NULL,
    crosses_midnight       BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS dim_failure_reason (
    failure_reason_id      INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    failure_category       VARCHAR(100) NOT NULL,
    failure_reason         VARCHAR(255) NOT NULL,
    planned_flag           BOOLEAN NOT NULL,
    source_reason_code     VARCHAR(100),
    source_dataset_id      INTEGER REFERENCES dim_source_dataset(source_dataset_id)
);

CREATE TABLE IF NOT EXISTS dim_utility (
    utility_id             INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    utility_code           VARCHAR(50) NOT NULL UNIQUE,
    utility_name           VARCHAR(100) NOT NULL,
    default_unit           VARCHAR(50),
    utility_category       VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_time (
    date_id                INTEGER PRIMARY KEY,
    calendar_date          DATE NOT NULL UNIQUE,
    year                   INTEGER NOT NULL,
    quarter                INTEGER NOT NULL,
    month                  INTEGER NOT NULL,
    month_name             VARCHAR(20) NOT NULL,
    week_of_year           INTEGER NOT NULL,
    day_of_month           INTEGER NOT NULL,
    day_of_week            INTEGER NOT NULL,
    day_name               VARCHAR(20) NOT NULL,
    is_weekend             BOOLEAN NOT NULL
);
