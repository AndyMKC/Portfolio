# Define input variables for configuration reuse
variable "project_id" {
  description = "The ID of the Google Cloud Project."
  type        = string
}

variable "region" {
  description = "The region for regional resources (Cloud Run, Firestore location)."
  type        = string
  # Note: us-central1 is often a safe bet for free tier services.
  # default     = "us-west1" # Using the region defined in the bootstrap job for consistency
}

variable "zone" {
  description = "The zone for regional resources (Cloud Run, Firestore location)."
  type        = string
  # Note: us-central1 is often a safe bet for free tier services.
  # default     = "us-west1-a" # Using the region defined in the bootstrap job for consistency
}

variable "service_name" {
  description = "The name for the Cloud Run service and the Docker image repository."
  type        = string
  default     = "storyspark-api"
}

variable "tfstate_bucket_name" {
  description = "The GCS bucket created by the bootstrap job to store the remote state."
  type        = string
  default     = "storyspark-555555-terraform-state"
}
