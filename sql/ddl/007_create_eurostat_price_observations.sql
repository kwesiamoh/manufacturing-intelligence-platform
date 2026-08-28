-- Stage 6C.2 — Structured Eurostat non-household electricity-price benchmark.

CREATE TABLE IF NOT EXISTS ref_eurostat_electricity_price_observation (
    price_observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_dataset_id INTEGER NOT NULL REFERENCES dim_source_dataset(source_dataset_id),

    dataset_code VARCHAR(32) NOT NULL,
    geo_code VARCHAR(8) NOT NULL,
    geo_name TEXT,
    period_code VARCHAR(16) NOT NULL,

    frequency_code VARCHAR(8),
    energy_product_code VARCHAR(32),

    consumption_band_code VARCHAR(32) NOT NULL,
    consumption_band_label TEXT,

    unit_code VARCHAR(16) NOT NULL,
    unit_label TEXT,

    tax_code VARCHAR(16) NOT NULL,
    tax_label TEXT,

    currency_code VARCHAR(16) NOT NULL,
    currency_label TEXT,

    price_value NUMERIC NOT NULL,
    status_code VARCHAR(16),

    data_class VARCHAR(64) NOT NULL,
    integration_role VARCHAR(64) NOT NULL,

    UNIQUE (
        source_dataset_id,
        dataset_code,
        geo_code,
        period_code,
        consumption_band_code,
        unit_code,
        tax_code,
        currency_code
    )
);

CREATE INDEX IF NOT EXISTS idx_eurostat_electricity_price_geo_period
    ON ref_eurostat_electricity_price_observation(geo_code, period_code);
