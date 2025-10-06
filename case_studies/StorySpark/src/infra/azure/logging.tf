resource "azurerm_log_analytics_workspace" "log_analytics_workspace" {
  name                = local.log_analytics_workspace_name
  location            = local.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "PerGB2018"
  # if an issue with the sku, it may be pergb2018
  retention_in_days   = 30
  tags                = local.tags
}

resource "azurerm_application_insights" "app_insights" {
  name                = local.application_insights_name
  location            = local.location
  resource_group_name = azurerm_resource_group.rg.name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.law.id
  tags                = local.tags
}
