# Local-to-AWS mapping

| Local project element | AWS target | Notes |
|---|---|---|
| `sources/.../bronze` | S3 Bronze | Raw/source-preserving data |
| `sources/.../silver` | S3 Silver | Cleaned source-domain datasets |
| future Gold outputs | S3 Gold | KPI and BI-ready datasets |
| Parquet files | S3 + Glue Catalog | Large analytical datasets |
| PostgreSQL 18 local | optional RDS PostgreSQL | Structured relational analytics |
| `pipelines/bronze` | Stage 9 ingestion jobs | Source acquisition |
| `pipelines/silver` | Stage 9 transformation jobs | Cleaning/conformance |
| `pipelines/postgres` | Stage 9 load jobs | Relational load |
| validation scripts | Stage 9 quality gates | Pipeline acceptance |
| local logs/stdout | CloudWatch Logs | Centralized execution logging |

## Important principle

Moving into AWS does not change source provenance.

Real benchmark data stays real benchmark data.
Synthetic enterprise data stays synthetic integration data.
External context stays external context.

Cloud deployment changes execution and storage location, not data meaning.
