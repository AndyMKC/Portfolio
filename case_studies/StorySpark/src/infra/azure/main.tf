terraform {
  required_version = ">= 1.3"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

resource "azurerm_search_service" "storyspark" {
  name                = var.search_name
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.search_sku
  replica_count       = var.search_replica_count
  partition_count     = var.search_partition_count

  # hosting_mode can be omitted if default; include if you need a value
  # hosting_mode = "default"
}

resource "azurerm_container_registry" "acr" {
  name                = var.acr_name
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.acr_sku
  admin_enabled       = false
}

data "azurerm_resource_group" "existing" {
  name = var.resource_group_name
}

data "azurerm_storage_account" "existing" {
  name                = var.storyspark_storage_account_name
  resource_group_name = data.azurerm_resource_group.existing.name
}

resource "azurerm_user_assigned_identity" "fn_identity" {
  name                = "${local.prefix}-fn-identity"
  resource_group_name = var.resource_group_name
  location            = var.location
}

resource "azurerm_role_assignment" "acr_pull" {
  principal_id         = azurerm_user_assigned_identity.fn_identity.principal_id
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
}

# Update your existing azurerm_function_app resource's site_config:
# linux_fx_version = "DOCKER|${azurerm_container_registry.acr.login_server}/storyspark:${var.image_tag}"
# and attach the user assigned identity

# If using existing resource group, use data.azurerm_resource_group.existing.* as shown earlier.

resource "azurerm_storage_account" "sa" {
  name                            = var.sa_name
  resource_group_name             = data.azurerm_resource_group.existing.name
  location                        = data.azurerm_resource_group.existing.location
  account_kind                    = "StorageV2"
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  allow_nested_items_to_be_public = false
  https_traffic_only_enabled      = true
}

resource "azurerm_service_plan" "sp" {
  name                = var.azurerm_service_plan_name
  resource_group_name = data.azurerm_resource_group.existing.name
  location            = data.azurerm_resource_group.existing.location

  # provider-specific args (os_type, reserved) for Linux plans may be needed
  os_type = "Linux"
  sku_name = "Y1"
}

resource "azurerm_function_app" "fn" {
  name                       = var.function_name
  resource_group_name        = data.azurerm_resource_group.existing.name
  location                   = data.azurerm_resource_group.existing.location
  app_service_plan_id        = azurerm_service_plan.sp.id
  storage_account_name       = azurerm_storage_account.sa.name
  storage_account_access_key = azurerm_storage_account.sa.primary_access_key
  version                    = "~4"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.fn_identity.id]
  }

  site_config {
    linux_fx_version = "DOCKER|${azurerm_container_registry.acr.login_server}/storyspark:${var.image_tag}"
  }

  app_settings = {
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"
    "WEBSITE_RUN_FROM_PACKAGE"            = "0"
    "DOCKER_REGISTRY_SERVER_URL"          = "https://${azurerm_container_registry.acr.login_server}"
    "TRANSFORMERS_CACHE"                  = "/home/site/wwwroot/models"
    # include any other env vars you need
  }
}
