# Define input variables for configuration reuse
variable "project_id" {
  description = "The ID of the Google Cloud Project."
  type        = string
}

variable "location" {
  type        = string
  description = "BigQuery dataset location (region or multi-region like US)"
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

# variable "service_name" {
#   description = "The name for the Cloud Run service and the Docker image repository."
#   type        = string
#   default     = "storyspark-api"
# }

variable "tfstate_bucket_name" {
  description = "The GCS bucket created by the bootstrap job to store the remote state."
  type        = string
  default     = "storyspark-5555555-terraform-state"
}

# variable "dataset_id" {
#   description = "The unique ID for the BigQuery dataset."
#   type        = string
#   default     = "book_inventory_vectors"
# }

variable "git_branch" {
  description = "The name of the branch currently being deployed."
  type        = string
  default     = "andymkc/0000_00_00_fake_branch" # A safe default for non-main branches
}

variable "base_dataset_id" {
  type        = string
  description = "Base dataset id (will be suffixed with env)"
  default     = "storyspark_embeddings_ds"
}

variable "base_source_table_id" {
  type        = string
  description = "Base source table id"
  default     = "source_table_books"
}

variable "base_embeddings_table_id" {
  type        = string
  description = "Base embeddings table id"
  default     = "text_embeddings_books"
}

variable "cloud_run_image" {
  type        = string
  description = "Container image for Cloud Run service (public or from Artifact Registry). Example: gcr.io/cloudrun/hello"
  default     = "gcr.io/cloudrun/hello"
}

variable "api_key" {
  type        = string
  description = "Shared API key required by the service (Option A: single secret). Set via CI or terraform var injection."
  default     = "replace-with-real-key"
}

variable "artifact_repo_id" {
  type        = string
  description = "Artifact Registry repository id (name)"
  default     = ""
}

variable "ci_service_account_email" {
  type        = string
  description = "Email of an existing GCP service account used by CI (e.g. github-actions-ci@PROJECT.iam.gserviceaccount.com)"
  default     = "github-terraform-sa@storyspark-5555555.iam.gserviceaccount.com"
}