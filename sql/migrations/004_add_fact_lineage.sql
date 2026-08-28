-- fact lineage schema alignment
-- Preserve synthetic lineage when loading facts.

ALTER TABLE fact_production
    ADD COLUMN IF NOT EXISTS source_record_id VARCHAR(64);

ALTER TABLE fact_downtime
    ADD COLUMN IF NOT EXISTS source_record_id VARCHAR(64),
    ADD COLUMN IF NOT EXISTS production_record_id VARCHAR(64);

ALTER TABLE fact_quality
    ADD COLUMN IF NOT EXISTS source_record_id VARCHAR(64),
    ADD COLUMN IF NOT EXISTS production_record_id VARCHAR(64);

ALTER TABLE fact_maintenance
    ADD COLUMN IF NOT EXISTS source_record_id VARCHAR(64),
    ADD COLUMN IF NOT EXISTS downtime_event_id VARCHAR(64),
    ADD COLUMN IF NOT EXISTS production_record_id VARCHAR(64);

ALTER TABLE fact_energy
    ADD COLUMN IF NOT EXISTS source_record_id VARCHAR(64),
    ADD COLUMN IF NOT EXISTS production_record_id VARCHAR(64);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fact_production_source_record
    ON fact_production(source_dataset_id, source_record_id)
    WHERE source_record_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_fact_downtime_source_record
    ON fact_downtime(source_dataset_id, source_record_id)
    WHERE source_record_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_fact_quality_source_record
    ON fact_quality(source_dataset_id, source_record_id)
    WHERE source_record_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_fact_maintenance_source_record
    ON fact_maintenance(source_dataset_id, source_record_id)
    WHERE source_record_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_fact_energy_source_record
    ON fact_energy(source_dataset_id, source_record_id)
    WHERE source_record_id IS NOT NULL;
