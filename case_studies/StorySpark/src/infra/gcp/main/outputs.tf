# output "api_endpoint" {
#   description = "The public URL endpoint for the Cloud Run service."
#   value       = google_cloud_run_v2_service.api_service.uri
# }

# output "artifact_registry_url" {
#   description = "The full URL for the Docker Artifact Registry."
#   value       = google_artifact_registry_repository.api_repo.name
# }

# output "dataset_id" {
#   description = "The fully qualified ID of the BigQuery Dataset."
#   value       = google_bigquery_dataset.vector_dataset.id
# }

# output "vertex_connection_sa_id" {
#   description = "The Service Account ID for the BigQuery Connection. This SA needs the 'Vertex AI User' role (roles/aiplatform.user) to allow the embedding model to work."
#   value       = google_bigquery_connection.vertex_connection.cloud_resource[0].service_account_id
# }

output "env" {
  value = local.env_suffix
}

output "dataset_id" {
  value = google_bigquery_dataset.embeddings.dataset_id
}

output "source_table_fqn" {
  value = "${var.project_id}.${google_bigquery_dataset.embeddings.dataset_id}.${google_bigquery_table.source_table.table_id}"
}

output "embeddings_table_fqn" {
  value = "${var.project_id}.${google_bigquery_dataset.embeddings.dataset_id}.${google_bigquery_table.embeddings_table.table_id}"
}

output "cloud_run_url" {
  value = google_cloud_run_service.storyspark_service.status[0].url
}

output "service_account_bq_vertex" {
  value = local.sa_bq_vertex.email + "@" + local.service_account_suffix
}

output "service_account_cloudrun" {
  value = local.sa_cloudrun.email + "@" + local.service_account_suffix
}

output "branch_name" {
  value = var.git_branch
}
