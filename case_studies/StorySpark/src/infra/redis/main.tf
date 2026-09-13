# Redis Cloud Essentials Subscription and Database
# Creates a Redis database on Redis Cloud (redis.io) using the perpetually free tier plan

# Create an Essentials subscription using the free plan
resource "rediscloud_essentials_subscription" "storyspark_redis" {
  name      = var.database_name
  plan_id   = data.rediscloud_essentials_plan.free_plan.id
}

# Create a database within the Essentials subscription
resource "rediscloud_essentials_database" "storyspark_redis_db" {
  subscription_id     = rediscloud_essentials_subscription.storyspark_redis.id
  name                = var.database_name
  data_persistence    = "none"
  replication         = false
  enable_default_user = true
  password            = ""  # Auto-generated if empty string
}

# Outputs are defined in outputs.tf