terraform {
  required_version = ">= 1.6.0"
}

variable "deployment_mode" {
  type        = string
  description = "Keep as documentation_only for the zero-cost portfolio build."
  default     = "documentation_only"

  validation {
    condition     = var.deployment_mode == "documentation_only"
    error_message = "The zero-cost portfolio configuration must remain in documentation_only mode."
  }
}

variable "aws_region" {
  type        = string
  description = "Documented target AWS region for a future deployment."
  default     = "eu-central-1"
}

locals {
  aws_target_architecture = {
    storage        = "Amazon S3 Bronze / Silver / Gold"
    catalog        = "AWS Glue Data Catalog"
    orchestration  = "AWS Step Functions / Glue"
    logging        = "Amazon CloudWatch"
    security       = "IAM / KMS / Secrets Manager"
    database       = "Amazon RDS for PostgreSQL"
    target_region  = var.aws_region
  }
}

# Zero-cost portfolio mode:
#
# No AWS resources are provisioned by this active Terraform configuration.
#
# The AWS target architecture is documented in the repository and can be
# activated through a separate deployment configuration in the future.