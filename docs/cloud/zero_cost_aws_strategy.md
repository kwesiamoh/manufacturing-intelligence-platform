# Zero-cost AWS deployment decision

## Constraint

The portfolio project must not incur AWS charges.

## Decision

The active Terraform configuration remains in:

`deployment_mode = "documentation_only"`

No AWS resources are created in this mode.

The AWS production architecture remains part of the portfolio documentation, but the working implementation continues locally using Python, Parquet, PostgreSQL, PowerShell, and Terraform validation.

This demonstrates infrastructure-as-code structure, cloud architecture mapping, AWS service selection, security/storage-zone design, and deployability planning without pretending paid resources were actually provisioned.

## Earlier Stage 8A package

The earlier Terraform configuration included legitimate production resources such as customer-managed KMS, Secrets Manager, and optional RDS. Those remain reasonable production choices, but they are not required for this strict zero-cost portfolio build.

## Terraform lock file

`.terraform.lock.hcl` should be committed to Git. It records the provider versions selected by `terraform init` and improves reproducibility.

It is therefore intentionally not excluded in the corrected `.gitignore`.
