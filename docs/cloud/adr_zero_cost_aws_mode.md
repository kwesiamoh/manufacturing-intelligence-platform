# Architecture decision record: zero-cost AWS mode

## Decision

The portfolio project will remain in a zero-cost AWS documentation and infrastructure-as-code mode.

## Reason

The project owner does not want to incur cloud charges.

## Consequence

The project demonstrates:

- AWS architecture design;
- infrastructure-as-code;
- service mapping;
- deployment planning;
- security architecture;
- cost-aware design.

It does not claim:

- production deployment on AWS;
- live AWS workloads;
- live S3 data lake operation;
- live Glue processing;
- live RDS hosting.

## Portfolio wording

Use:

- AWS-ready architecture
- AWS target architecture
- Terraform-defined cloud infrastructure
- cloud deployment design
- future AWS deployment path

Do not use:

- deployed on AWS
- hosted on AWS
- running in AWS

unless a future deployment is actually performed.
