variable "subscription_id" {
  description = "Azure subscription id"
  type        = string
  default     = "5ab40d90-e237-422e-a575-b5b73033077c"
}

variable "resource_group_name" {
  description = "Resource group"
  type        = string
  default     = "StorySparkResourceGroup"
}

variable "location" {
  description = "Azure region"
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

variable "image_tag" {
  type        = string
  description = "Docker image tag pushed to ACR (CI should override with immutable tag)"
  #default     = "latest"
}

variable "acr_sku" {
  type    = string
  default = "Basic"
}

variable "acr_name" {
  type        = string
  description = "Name for the Azure Container Registry"
  default     = "storysparkacr" # change or override in tfvars/CI
}

variable "function_name" {
  type        = string
  description = "Name for the Function App"
  default     = "StorySparkAPIGateway"
}

variable "azurerm_service_plan_name" {
  type        = string
  description = "Existing App Service Plan name"
  default     = "WestUS2LinuxDynamicPlan"
}

variable "storyspark_storage_account_name" {
  type        = string
  description = "Existing storage account to use"
  default     = "storysparkstorageacct"
}

variable "sa_name" {
  description = "Storage account name used for StorySpark"
  type        = string
  default     = "storysparkstorageacct"
}

variable "functions_worker_runtime" {
  description = "Functions worker runtime"
  type        = string
  default     = "python"
}

variable "app_port" {
  description = "Port your container listens on; set same value inside Dockerfile"
  type        = number
  default     = 80
}

variable "image_repo" {
  description = "Repository name inside ACR"
  type        = string
  default     = "storyspark"
}
