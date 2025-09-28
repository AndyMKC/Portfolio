output "search_service_id" {
  value = azurerm_search_service.storyspark.id
}

output "search_service_name" {
  value = azurerm_search_service.storyspark.name
}

output "search_location" {
  value = azurerm_search_service.storyspark.location
}

output "search_sku" {
  value = azurerm_search_service.storyspark.sku
}

output "replica_count" {
  value = azurerm_search_service.storyspark.replica_count
}

output "partition_count" {
  value = azurerm_search_service.storyspark.partition_count
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
