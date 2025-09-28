output "search_service_endpoint" {
  description = "The REST endpoint for the Azure Cognitive Search service"
  # build the endpoint from the service name
  value = "https://${azurerm_search_service.search.name}.search.windows.net"
}

output "primary_api_key" {
  description = "Primary admin key for the Azure Cognitive Search service"
  value       = azurerm_search_service.search.primary_key
  sensitive   = true
}

output "secondary_api_key" {
  description = "Secondary admin key for the Azure Cognitive Search service"
  value       = azurerm_search_service.search.secondary_key
  sensitive   = true
}