resource "azurerm_container_registry" "container_registry" {
  name                   = local.acr_name
  resource_group_name    = azurerm_resource_group.rg.name
  location               = local.location
  sku                    = "Basic"
  admin_enabled          = var.acr_admin_enabled
  anonymous_pull_enabled = false
  tags                   = local.tags
}

# Optional: list of repositories is managed outside Terraform (CI pushes images)
# If you enable admin user for initial bootstrapping, do not commit credentials; use CI secrets.

data "azurerm_container_registry" "acr_data" {
  name                = azurerm_container_registry.container_registry.name
  resource_group_name = azurerm_resource_group.rg.name
}

output "acr_login_server" {
  value = data.azurerm_container_registry.acr_data.login_server
}

output "acr_name" {
  value = azurerm_container_registry.container_registry.name
}
