# Future AWS deployment path

## Phase 1: foundation

Deploy:
- S3 Bronze/Silver/Gold
- IAM roles/policies
- basic logging

## Phase 2: metadata and ingestion

Add:
- Glue Data Catalog
- crawlers where useful
- scheduled ingestion jobs

## Phase 3: orchestration

Add:
- Step Functions or equivalent orchestration
- data-quality gates
- retry and failure handling

## Phase 4: analytics database

Optional:
- RDS PostgreSQL

This should only be enabled if the portfolio owner accepts the cost model.

## Phase 5: BI

Connect:
- Power BI to RDS or exported Gold datasets

## Migration rule

Source provenance must remain unchanged during cloud migration.

Real benchmark data remains real benchmark data.

Synthetic enterprise data remains synthetic integration data.

External context remains external context.
