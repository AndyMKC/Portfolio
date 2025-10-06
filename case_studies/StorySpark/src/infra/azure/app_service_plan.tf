resource "azurerm_service_plan" "app_service_plan" {
  name                = local.app_service_plan_name
  location            = local.location
  resource_group_name = azurerm_resource_group.rg.name
  os_type             = "Linux"
  sku_name            = "Y1"
  kind                = "Linux"
  reserved            = true
  tags                = local.tags

  sku {
    tier = "Dynamic"
    size = "Y1"
  }
}
