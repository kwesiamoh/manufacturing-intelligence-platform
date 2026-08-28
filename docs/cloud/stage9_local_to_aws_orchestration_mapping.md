# Local orchestration to AWS target mapping

The project currently runs locally and incurs no AWS cost. The AWS portion remains a documented target architecture only.

| Local implementation | Future AWS target role | Current status |
|---|---|---|
| Bronze source folders | Amazon S3 Bronze zone | Documented target only |
| Silver Parquet folders | Amazon S3 Silver zone | Documented target only |
| PostgreSQL analytics database | Amazon RDS for PostgreSQL | Documented target only |
| PowerShell/Python pipeline runner | AWS Step Functions / AWS Glue orchestration pattern | Documented target only |
| Python ingestion and DQ scripts | AWS Glue jobs or containerized tasks | Documented target only |
| SQL analytics views | RDS PostgreSQL analytical layer | Documented target only |
| Local logs and JSON manifests | CloudWatch Logs / S3 operational logs | Documented target only |
| Local configuration and credentials | IAM roles / Secrets Manager | Documented target only |

## Important wording

Accurate portfolio language:

- AWS-ready architecture
- AWS target architecture
- Terraform-defined cloud design
- local production-style orchestration
- future deployable AWS path

Do not describe the platform as deployed, hosted or running on AWS unless live cloud resources are actually created later.

## Cost position

The current project mode remains zero-cost. No AWS resources are required for Stage 9.
