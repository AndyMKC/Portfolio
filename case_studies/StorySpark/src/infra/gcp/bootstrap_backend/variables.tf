#
# Terraform Variables for the Bootstrap Backend
#

# The Google Cloud Project ID (e.g., storyspark-555555)
variable "project_id" {
  description = "The ID of the GCP project where resources will be created."
  type        = string
}

# The desired region for the GCS bucket (e.g., us-west1)
variable "region" {
  description = "The region for the GCS backend bucket."
  type        = string
}

# The desired zone for the GCS bucket (e.g., us-west1)
variable "zone" {
  description = "The region for the GCS backend bucket."
  type        = string
}

# The name of the GCS bucket to store the Terraform state (e.g., storyspark-555555-terraform-state)
variable "tfstate_bucket_name" {
  description = "The globally unique name for the GCS bucket used for Terraform state storage."
  type        = string
}

variable "create_dev" {
  description = "Create dev service accounts"
  type        = bool
  default     = true
}

variable "create_prod" {
  description = "Create prod service accounts"
  type        = bool
  default     = true
}

variable "dev_suffix" {
  type    = string
  default = "dev"
}

variable "prod_suffix" {
  type    = string
  default = "prod"
}

