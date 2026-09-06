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

# variable "tfstate_bucket_name" {
#   description = "The GCS bucket created by the bootstrap job to store the remote state."
#   type        = string
#   default     = "storyspark-5555555-terraform-state"
# }

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
  default     = "storyspark_dataset"
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
  description = "Container image reference for Cloud Run. Must be the immutable digest form: REGION-docker.pkg.dev/PROJECT/REPO/IMAGE@sha256:..."
  validation {
    condition     = can(regex("^[a-z0-9-]+-docker\\.pkg\\.dev/.+@sha256:[0-9a-f]{64}$", var.cloud_run_image))
    error_message = "cloud_run_image must be an Artifact Registry digest reference (e.g. us-west1-docker.pkg.dev/project/repo/image@sha256:...)."
  }
}

variable "api_key" {
  type        = string
  description = "Shared API key required by the service (Option A: single secret). Set via CI or terraform var injection."
  default     = "replace-with-real-key"
}

variable "artifact_docker_images_repo_id" {
  type        = string
  description = "For Docker Images"
  default     = "containers"
}

# variable "artifact_exported_model_repo_id" {
#   type        = string
#   description = "For Exported Models"
#   default     = "models"
# }

variable "ci_service_account_email" {
  type        = string
  description = "Email of an existing GCP service account used by CI (e.g. github-actions-ci@PROJECT.iam.gserviceaccount.com)"
  default     = "github-terraform-sa@storyspark-5555555.iam.gserviceaccount.com"
}

variable "model_export_bucket" {
  type        = string
  description = "GCS bucket to store exported models"
}

variable "model_export_bucket_volume_name" {
  type        = string
  description = "Folder name that we use to denote this volume mount"
}

# ── Redis Cloud Variables (for distributed rate limiting) ──────────────

variable "rediscloud_api_key" {
  description = "Redis Cloud API Key (public key). Inject from GitHub secret REDIS_API_KEY."
  type        = string
  default     = ""
}

variable "rediscloud_api_secret" {
  description = "Redis Cloud API Secret (private key). Inject from GitHub secret REDIS_API_SECRET."
  type        = string
  default     = ""
  sensitive   = true
}

variable "redis_database_name" {
  description = "Name of the Redis database for rate limiting"
  type        = string
  default     = "storyspark-redis"
}

variable "redis_cloud_provider" {
  description = "Cloud provider for the Redis database (default: GCP for same-cloud deployment)"
  type        = string
  default     = "GCP"
}

variable "redis_region" {
  description = "Region for the Redis database (GCP us-west1 supports free tier)"
  type        = string
  default     = "us-west1"
}

# Size in MB for the free tier plan (Redis Cloud free tier is 30MB)
variable "redis_free_plan_size_mb" {
  description = "Size of the free tier plan in MB. Redis Cloud free tier is 30MB."
  type        = number
  default     = 30
}