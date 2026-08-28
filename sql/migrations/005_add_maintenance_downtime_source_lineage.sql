-- source-qualified reliability: Source-qualified maintenance -> downtime lineage
--
-- fact_maintenance.source_dataset_id identifies the maintenance record's
-- source.  It must not be assumed to identify the referenced downtime event's
-- source for every future integration.  Store that referenced source
-- explicitly and enforce the composite downtime lineage when it is supplied.

ALTER TABLE public.fact_maintenance
    ADD COLUMN IF NOT EXISTS downtime_source_dataset_id INTEGER;

-- Existing Velora synthetic maintenance and downtime are generated and loaded
-- from the same SYNTHETIC_ENTERPRISE source.  This is a deterministic backfill
-- for those established links; it does not guess across sources.
UPDATE public.fact_maintenance m
SET downtime_source_dataset_id = m.source_dataset_id
WHERE m.downtime_source_dataset_id IS NULL
  AND m.downtime_event_id IS NOT NULL
  AND EXISTS (
      SELECT 1
      FROM public.fact_downtime d
      WHERE d.source_dataset_id = m.source_dataset_id
        AND d.source_record_id = m.downtime_event_id
  );

CREATE UNIQUE INDEX IF NOT EXISTS uq_fact_downtime_source_lineage
    ON public.fact_downtime(source_dataset_id, source_record_id);

CREATE INDEX IF NOT EXISTS idx_fact_maintenance_downtime_lineage
    ON public.fact_maintenance(
        downtime_source_dataset_id,
        downtime_event_id
    );

DO $migration$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.fact_maintenance'::regclass
          AND conname = 'fk_fact_maintenance_downtime_lineage'
    ) THEN
        ALTER TABLE public.fact_maintenance
            ADD CONSTRAINT fk_fact_maintenance_downtime_lineage
            FOREIGN KEY (downtime_source_dataset_id, downtime_event_id)
            REFERENCES public.fact_downtime(source_dataset_id, source_record_id)
            NOT VALID;
    END IF;
END
$migration$;

ALTER TABLE public.fact_maintenance
    VALIDATE CONSTRAINT fk_fact_maintenance_downtime_lineage;

COMMENT ON COLUMN public.fact_maintenance.downtime_source_dataset_id IS
    'Source dataset of the downtime event referenced by downtime_event_id; distinct from the maintenance record source_dataset_id.';
