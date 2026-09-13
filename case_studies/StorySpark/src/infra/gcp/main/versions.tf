terraform {
  required_version = ">= 1.2.0"

  # The GCS backend configuration is left empty here.
  # The bucket name and prefix will be injected via the 
  # 'init' command in GitHub Actions using -backend-config.
  backend "gcs" {}

    required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.13.0"
    }

    # Using google-beta is necessary for newer Cloud Run features (V2/2nd Gen)
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 7.13.0"
    }

        # Redis Cloud provider for managed Redis database (rate limiting)
    rediscloud = {
      source  = "RedisLabs/rediscloud"
      version = "~> 1.0"
    }
  }
}

#
# GCP Provider Configuration
#
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

#
# Redis Cloud Provider Configuration
# Uses API key (public) and API secret (private) for authentication.
# Both should be provided as terraform variables, typically injected from
# GitHub secrets during CI/CD (REDIS_API_KEY and REDIS_API_SECRET).
#
provider "rediscloud" {
  api_key    = var.rediscloud_api_key
  secret_key = var.rediscloud_api_secret
}

# Data source to find the free Essentials plan
data "rediscloud_essentials_plan" "free_plan" {
  cloud_provider        = var.redis_cloud_provider
  region                = var.redis_region
  size                  = var.redis_free_plan_size_mb
  size_measurement_unit = "MB"
}
