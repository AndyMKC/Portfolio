# Terraform and Provider Version Constraints

terraform {
  required_version = ">= 1.2.0"

  required_providers {
    rediscloud = {
      source  = "RedisLabs/rediscloud"
      version = "~> 1.0"
    }
  }
}

# Configure the Redis Cloud Provider
# The provider requires both an API Key (public) and API Secret (private)
# These should be passed via environment variables or terraform variables:
#   REDISCLOUD_ACCESS_KEY - Public API key (stored in GitHub secrets as REDIS_API_KEY)
#   REDISCLOUD_SECRET_KEY - Private API secret (stored in GitHub secrets as REDIS_API_SECRET)
provider "rediscloud" {
  api_key    = var.rediscloud_api_key
  secret_key = var.rediscloud_api_secret
}

# Data source to find the free Essentials plan
# Uses size + cloud_provider + region to find the free tier plan (30MB)
data "rediscloud_essentials_plan" "free_plan" {
  cloud_provider          = var.cloud_provider
  region                  = var.region
  size                    = var.free_plan_size_mb
  size_measurement_unit   = "MB"
}