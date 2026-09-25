# Redis Cloud Essentials Subscription and Database
# Creates a Redis database on Redis Cloud (redis.io) using the perpetually free tier plan

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
  cloud_provider        = var.cloud_provider
  region                = var.region
  size                  = var.free_plan_size_mb
  size_measurement_unit = "MB"
}

# Create an Essentials subscription using the free plan
resource "rediscloud_essentials_subscription" "storyspark_redis" {
  name    = var.database_name
  plan_id = data.rediscloud_essentials_plan.free_plan.id
}

# Create a database within the Essentials subscription
resource "rediscloud_essentials_database" "storyspark_redis_db" {
  subscription_id     = rediscloud_essentials_subscription.storyspark_redis.id
  name                = var.database_name
  data_persistence    = "none"
  replication         = false
  enable_default_user = true
  password            = "" # Auto-generated if empty string
}

# Outputs are defined in outputs.tf