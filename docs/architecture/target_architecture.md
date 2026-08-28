# Target Architecture

## Current implemented environment

The working portfolio implementation is local:

`Public/benchmark sources -> Bronze -> Silver Parquet -> PostgreSQL -> Gold/analytics views -> Power BI`

Python and SQL perform the transformation and analytical workloads.

## Target cloud architecture

The project includes an AWS-ready target architecture and Terraform-defined
infrastructure patterns.

A representative target design is:

`Sources -> S3 Bronze -> ETL/Orchestration -> S3 Silver -> analytical database -> Gold semantic layer -> Power BI`

Supporting controls would include:

- IAM least privilege;
- encryption at rest and in transit;
- logging/monitoring;
- secrets management;
- infrastructure as code;
- environment separation.

## AWS deployment status

**No live AWS resources are deployed.**

The project maintains a hard **€0 AWS spend limit**.

Therefore approved wording is:

- AWS-ready
- target AWS architecture
- Terraform-defined
- infrastructure-as-code design

Do not use:

- hosted on AWS
- deployed on AWS
- running in AWS
- production AWS environment

unless that status changes in the future.

## Local-to-cloud mapping

| Local component | Target AWS analogue |
|---|---|
| Bronze folders | S3 Bronze |
| Silver Parquet | S3 Silver |
| Python orchestration | Glue/Lambda/ECS/Step Functions depending workload |
| PostgreSQL | RDS/Aurora or analytical warehouse depending target design |
| local secrets | Secrets Manager / Parameter Store |
| local logs | CloudWatch / centralized logging |
| Power BI Desktop | Power BI Service with controlled gateway/connectivity |

The mapping is architectural, not deployed implementation evidence.
