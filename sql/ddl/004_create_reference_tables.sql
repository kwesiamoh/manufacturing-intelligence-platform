-- reference data reference/benchmark tables
-- These tables intentionally remain separate from the fictional enterprise facts.

CREATE TABLE IF NOT EXISTS ref_itac_assessment (
    ref_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_dataset_id INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    source_row_json JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS ref_itac_recommendation (
    ref_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_dataset_id INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    source_row_json JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS ref_fmucd_maintenance (
    ref_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_dataset_id INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    source_row_json JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS ref_statcan_water (
    ref_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_dataset_id INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    source_row_json JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS ref_eia_mecs (
    ref_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_dataset_id INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    source_table VARCHAR(100) NOT NULL,
    source_sheet VARCHAR(100) NOT NULL,
    source_row_json JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS ref_eu_ets (
    ref_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_dataset_id INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    source_row_json JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS ref_eurostat_energy_price (
    ref_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_dataset_id INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),
    dataset_code VARCHAR(32) NOT NULL,
    source_row_json JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ref_itac_assessment_source
    ON ref_itac_assessment(source_dataset_id);

CREATE INDEX IF NOT EXISTS idx_ref_itac_recommendation_source
    ON ref_itac_recommendation(source_dataset_id);

CREATE INDEX IF NOT EXISTS idx_ref_fmucd_source
    ON ref_fmucd_maintenance(source_dataset_id);

CREATE INDEX IF NOT EXISTS idx_ref_statcan_source
    ON ref_statcan_water(source_dataset_id);

CREATE INDEX IF NOT EXISTS idx_ref_mecs_source
    ON ref_eia_mecs(source_dataset_id);

CREATE INDEX IF NOT EXISTS idx_ref_euets_source
    ON ref_eu_ets(source_dataset_id);

CREATE INDEX IF NOT EXISTS idx_ref_eurostat_source
    ON ref_eurostat_energy_price(source_dataset_id);
