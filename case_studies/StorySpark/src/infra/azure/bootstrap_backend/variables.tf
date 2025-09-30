variable "subscription_id" {
  description = "Azure subscription id"
  type        = string
}

variable "location" {
  description = "Azure region for bootstrap resources"
  type        = string
  default     = "westus2"
}

variable "rg_name" {
  description = "Existing or desired resource group for bootstrap backend"
  type        = string
  default     = "StorySparkResourceGroup"
}

variable "sa_name" {
  description = "Storage account name used for Terraform state (lowercase, 3-24 chars)"
  type        = string
  default     = "bootstrapbackend"
}

variable "container_name" {
  description = "Blob container name for tfstate"
  type        = string
  default     = "tfstate"
}
