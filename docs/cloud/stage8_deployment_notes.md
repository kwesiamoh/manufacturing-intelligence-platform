# Stage 8 deployment notes

## Prerequisites

Install:
- AWS CLI
- Terraform

Configure AWS credentials through the normal AWS CLI credential mechanism.

Do not place access keys in Terraform files or Git.

## Initialize

From:

`infrastructure\terraform`

run:

```powershell
terraform init
```

## Format

```powershell
terraform fmt -recursive
```

## Validate

```powershell
terraform validate
```

## Preview

```powershell
terraform plan -var-file="terraform.tfvars.example"
```

## Deploy

Only when you intentionally want to create AWS resources:

```powershell
terraform apply -var-file="terraform.tfvars.example"
```

## RDS

Do not enable RDS yet unless you specifically want to deploy a billable database.

The local PostgreSQL instance is sufficient while the AWS foundation and ingestion layer are being built.

## Destroy

For a temporary portfolio deployment:

```powershell
terraform destroy -var-file="terraform.tfvars.example"
```

Review the plan before confirming destructive operations.
