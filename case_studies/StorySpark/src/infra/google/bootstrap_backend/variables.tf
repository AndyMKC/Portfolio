variable "project_id" {
  type        = string
  description = "GCP Project ID where resources will be created"
}

variable "region" {
  type        = string
  description = "GCP region for regional resources. Choose the nearest regional location to Washington."
  default     = "us-west1"
}

variable "zone" {
  type        = string
  description = "GCP zone for zonal resources"
  default     = "us-west1-a"
}

variable "tfstate_bucket_name" {
  type        = string
  description = "Name of the GCS bucket to store Terraform state"
  default     = "storyspark-474223-terraform-state"
}
