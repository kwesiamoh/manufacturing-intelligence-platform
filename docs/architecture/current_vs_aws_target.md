# Implementation status: local platform vs AWS target

## Current implementation

The manufacturing intelligence platform is currently implemented locally using:

- Python pipelines
- Parquet Bronze/Silver outputs
- PostgreSQL 18
- SQL analytics views
- data-quality rules and validation scripts
- PowerShell orchestration
- Terraform in documentation-only mode

This is the working portfolio implementation.

## AWS target architecture

The platform is designed to map to AWS as follows:

| Current local component | AWS target |
|---|---|
| Bronze source folders | Amazon S3 Bronze zone |
| Silver Parquet datasets | Amazon S3 Silver zone |
| Gold analytical datasets | Amazon S3 Gold zone |
| Dataset metadata/schema tracking | AWS Glue Data Catalog |
| Local PostgreSQL 18 | Amazon RDS for PostgreSQL |
| Local pipeline runner | AWS Step Functions / Glue jobs / scheduled execution |
| Local stdout/log files | Amazon CloudWatch Logs |
| Local credential/config handling | AWS IAM + Secrets Manager |
| Local encryption/storage controls | AWS KMS + S3 encryption |
| Power BI connection | RDS / Gold analytical outputs |

## What has been deployed to AWS

Nothing.

The project intentionally uses a strict zero-cost configuration.

The active Terraform configuration provisions zero AWS resources.

## What has been validated

- Terraform installation
- Terraform initialization
- Terraform formatting
- Terraform configuration validation
- zero-resource Terraform plan

The validated plan returns no infrastructure changes.

## Future deployment

If the project is later deployed to AWS:

1. activate a deployment Terraform configuration;
2. review resource cost;
3. provision S3 and IAM first;
4. add Glue/Data Catalog;
5. add orchestration;
6. add RDS only if required;
7. migrate selected data;
8. verify logging, security, and cost controls.

The current local implementation is intentionally structured so this migration does not require redesigning the analytics logic.
