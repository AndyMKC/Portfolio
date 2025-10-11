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
variable "bucket_name" {
  description = "The globally unique name for the GCS bucket used for Terraform state storage."
  type        = string
}

# Note: The zone variable is not used for GCS buckets, so we omit it here.
