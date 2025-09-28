variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "westus2"
}

variable "resource_group_name" {
  description = "Name of the Resource Group"
  type        = string
  default     = "storysparkresourcegroup"
}

variable "search_service_name" {
  description = "Unique name for the Azure AI Search service"
  type        = string
  default     = "storyspark-ai-search"
}
