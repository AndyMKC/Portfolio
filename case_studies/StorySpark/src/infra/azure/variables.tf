variable "environment" {
  description = "Deployment environment tag"
  type        = string
  default     = "dev"
}

variable "subscription_id" {
  description = "Azure subscription id to deploy into"
  type        = string
}

variable "location" {
  description = "Azure region to deploy resources into"
  type        = string
  default     = "eastus"
}

variable "acr_admin_enabled" {
  description = "Set true to enable ACR admin user for initial deploy; not recommended long-term"
  type        = bool
  # Current one uses false
  default     = false
}

# variable "acr_admin_password" {
#   description = "Optional ACR admin password; prefer using GitHub Actions secrets instead"
#   type        = string
#   sensitive   = true
#   default     = ""
# }

variable "project_prefix" {
  description = "Prefix used for resource names"
  type        = string
  # TODO:  change this to StorySpark when done
  default     = "StorySpark2"
}

variable "resource_group" {
  description = "Name of the resource group to deploy all resources into"
  type        = string
  default     = "${var.project_prefix}ResourceGroup"
}

# variable "function_app_image" {
#   description = "Container image for the Function App in the format <registry>/<repo>:<tag>"
#   type        = string
#   # TODO:  change this to storysparkacr.azurecr.io/storysparkrepo:latest when done
#   default     = "storysparkacr2.azurecr.io/storysparkrepo2:latest"
# }

variable "acr_name" {
  description = "Container Registry name; defaults to derived value from project_prefix"
  type        = string
  default     = ""
}

variable "acr_repo" {
  description = "Repository name inside ACR"
  type        = string
  default     = "storysparkrepo"
}








# variable "bootstrap_backend_resource_group" {
#   description = "Resource group containing the bootstrapbackend storage account used for remote state"
#   type        = string
#   default     = "${var.resource_group}"
# }

# variable "bootstrap_backend_storage_account" {
#   description = "Storage account name used for remote state"
#   type        = string
#   default     = "bootstrapbackend"
# }

# variable "bootstrap_backend_container" {
#   description = "Container name inside the bootstrapbackend storage account used for tfstate"
#   type        = string
#   default     = "StorySpark"
# }

# variable "bootstrap_backend_key" {
#   description = "Key name inside the container used for tfstate"
#   type        = string
#   default     = "tfstate"
# }


