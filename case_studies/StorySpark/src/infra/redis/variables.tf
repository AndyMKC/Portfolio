# Terraform Variables for Redis Cloud Infrastructure

# Redis Cloud API Key (public key)
# This should be set via environment variable REDISCLOUD_API_KEY
# or passed as a terraform variable. In CI/CD, this comes from GitHub secrets (REDIS_API_KEY).
variable "rediscloud_api_key" {
  description = "Redis Cloud API Key (public key). Set via REDISCLOUD_API_KEY env var or GitHub secret REDIS_API_KEY."
  type        = string
  sensitive   = true
}

# Redis Cloud API Secret (private key)
# This should be set via environment variable REDISCLOUD_API_SECRET
# or passed as a terraform variable. In CI/CD, this should come from GitHub secrets (REDIS_API_SECRET).
variable "rediscloud_api_secret" {
  description = "Redis Cloud API Secret (private key). Set via REDISCLOUD_API_SECRET env var or GitHub secret REDIS_API_SECRET."
  type        = string
  sensitive   = true
}

# Database name
variable "database_name" {
  description = "Name of the Redis database to create"
  type        = string
  default     = "storyspark-redis"
}

# Cloud provider for the Redis database
# Defaults to GCP for same-cloud deployment with Cloud Run (us-west1)
variable "cloud_provider" {
  description = "Cloud provider for the Redis database (AWS, GCP, or AZURE)"
  type        = string
  default     = "GCP"
  validation {
    condition     = contains(["AWS", "GCP", "AZURE"], var.cloud_provider)
    error_message = "cloud_provider must be one of: AWS, GCP, AZURE"
  }
}

# Region for the Redis database
# Must be a region that supports the free tier (Essentials) for the selected cloud provider
# GCP free tier regions include: us-west1, us-central1, us-east1, us-east4, europe-west1,
#   europe-west2, europe-west3, europe-west4, asia-east1, asia-southeast1,
#   asia-northeast1, asia-south1, australia-southeast1
variable "region" {
  description = "Region for the Redis database (must support free tier for selected cloud provider)"
  type        = string
  default     = "us-west1"
}

# Memory limit in GB for the database
# Free tier typically supports up to 30MB (0.03 GB).
# Note: For Essentials subscriptions, the memory is determined by the plan,
# not by this variable. This variable is kept for Pay-As-You-Go databases.
variable "memory_limit_in_gb" {
  description = "Memory limit in GB for the database. Free tier supports up to 30MB (0.03 GB)."
  type        = number
  default     = 0.03
}

# Size in MB for the free tier plan (Redis Cloud free tier is 30MB)
variable "free_plan_size_mb" {
  description = "Size of the free tier plan in MB. Redis Cloud free tier is 30MB."
  type        = number
  default     = 30
}