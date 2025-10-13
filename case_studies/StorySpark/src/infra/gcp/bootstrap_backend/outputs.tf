output "bq_vertex_dev_email" {
  value       = try(google_service_account.bq_vertex_dev[0].email, "")
  description = "Email of the dev BigQuery/Vertex service account; empty if create_dev = false"
}

output "cloudrun_dev_email" {
  value       = try(google_service_account.cloudrun_dev[0].email, "")
  description = "Email of the dev Cloud Run service account; empty if create_dev = false"
}

output "bq_vertex_prod_email" {
  value       = try(google_service_account.bq_vertex_prod[0].email, "")
  description = "Email of the prod BigQuery/Vertex service account; empty if create_prod = false"
}

output "cloudrun_prod_email" {
  value       = try(google_service_account.cloudrun_prod[0].email, "")
  description = "Email of the prod Cloud Run service account; empty if create_prod = false"
}