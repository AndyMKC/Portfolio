/*
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}
*/

resource "azurerm_search_service" "search" {
  name                = var.search_service_name
  resource_group_name = var.resource_group_name
  location            = var.location

  sku             = "free" # options: free, basic, standard, storage_optimized_l1, etc.
  replica_count   = 1
  partition_count = 1

  # Optional: assign a managed identity
  # identity {
  #   type = "SystemAssigned"
  # }
}
