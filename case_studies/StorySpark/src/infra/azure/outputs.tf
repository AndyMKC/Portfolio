output "search_sku" {
  value = azurerm_search_service.storyspark.sku
}

output "replica_count" {
  value = azurerm_search_service.storyspark.replica_count
}

output "partition_count" {
  value = azurerm_search_service.storyspark.partition_count
}

output "search_service_id" {
  value = azurerm_search_service.storyspark.id
}

output "search_service_name" {
  value = azurerm_search_service.storyspark.name
}

output "search_location" {
  value = azurerm_search_service.storyspark.location
}

output "primary_admin_key" {
  value     = azurerm_search_service.storyspark.primary_key
  sensitive = true
}

output "secondary_admin_key" {
  value     = azurerm_search_service.storyspark.secondary_key
  sensitive = true
}

output "query_keys" {
  value = azurerm_search_service.storyspark.query_keys
}

output "acr_login_server" {
  value = azurerm_container_registry.acr.login_server
}

output "function_default_hostname" {
  description = "Function App default hostname"
  value       = azurerm_function_app.fn.default_hostname
}

output "deployed_image" {
  description = "Confirm which tag was applied"
  value = "${azurerm_container_registry.acr.login_server}/${var.image_repo}:${var.image_tag}"
}