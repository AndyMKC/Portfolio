# Outputs for Redis Cloud Infrastructure

output "subscription_id" {
  description = "The ID of the Redis Cloud subscription"
  value       = rediscloud_essentials_subscription.storyspark_redis.id
}

output "database_id" {
  description = "The ID of the created Redis database (db_id)"
  value       = rediscloud_essentials_database.storyspark_redis_db.db_id
}

output "database_endpoint" {
  description = "The public endpoint for the Redis database"
  value       = rediscloud_essentials_database.storyspark_redis_db.public_endpoint
}

output "database_name" {
  description = "The name of the Redis database"
  value       = rediscloud_essentials_database.storyspark_redis_db.name
}

output "database_status" {
  description = "The status of the Redis database"
  value       = rediscloud_essentials_subscription.storyspark_redis.status
}

# Construct a full connection string for easy use
output "redis_connection_string" {
  description = "Full Redis connection string (rediss://:password@endpoint:port)"
  value       = "rediss://:${rediscloud_essentials_database.storyspark_redis_db.password}@${rediscloud_essentials_database.storyspark_redis_db.public_endpoint}"
  sensitive   = true
}

# Also provide individual components for flexible configuration
output "redis_host" {
  description = "Redis host (endpoint)"
  value       = rediscloud_essentials_database.storyspark_redis_db.public_endpoint
}

output "redis_username" {
  description = "Redis username (default user for Redis Cloud Essentials)"
  value       = "default"
}

output "redis_password" {
  description = "Redis password (sensitive)"
  value       = rediscloud_essentials_database.storyspark_redis_db.password
  sensitive   = true
}