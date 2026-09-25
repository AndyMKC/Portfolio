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