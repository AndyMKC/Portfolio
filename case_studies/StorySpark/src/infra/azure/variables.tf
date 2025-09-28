variable "subscription_id" {
  description = "Azure subscription id"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group containing the search service"
  type        = string
  default     = "StorySparkResourceGroup"
}

variable "location" {
  description = "Azure region for the Search service"
  type        = string
  default     = "westus2"
}

variable "search_name" {
  description = "Name of the Cognitive Search service"
  type        = string
  default     = "storyspark-ai-search"
}

variable "search_sku" {
  description = "SKU for the Search service"
  type        = string
  default     = "free"
}

variable "search_replica_count" {
  description = "Number of replicas"
  type        = number
  default     = 1
}

variable "search_partition_count" {
  description = "Number of partitions"
  type        = number
  default     = 1
}
