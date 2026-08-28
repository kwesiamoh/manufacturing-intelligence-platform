-- Stage 7A — Core data quality framework

CREATE TABLE IF NOT EXISTS dq_rule (
    dq_rule_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    rule_code VARCHAR(100) NOT NULL UNIQUE,
    rule_name TEXT NOT NULL,
    domain_name VARCHAR(100) NOT NULL,
    target_object VARCHAR(150) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    active_flag BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS dq_result (
    dq_result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dq_rule_id BIGINT NOT NULL REFERENCES dq_rule(dq_rule_id),
    run_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_dataset_id INTEGER REFERENCES dim_source_dataset(source_dataset_id),
    target_object VARCHAR(150) NOT NULL,
    evaluated_row_count BIGINT,
    failed_row_count BIGINT NOT NULL,
    failure_rate NUMERIC,
    result_status VARCHAR(20) NOT NULL,
    result_detail TEXT
);

CREATE INDEX IF NOT EXISTS idx_dq_result_rule_run
    ON dq_result(dq_rule_id, run_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_dq_result_status
    ON dq_result(result_status);
