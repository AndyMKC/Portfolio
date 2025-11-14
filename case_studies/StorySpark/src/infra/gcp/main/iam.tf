# Grant the existing CI service account permission to push images.
# This is a project-level binding granting roles/artifactregistry.writer to the provided SA email.
# If you prefer narrower scope, use google_artifact_registry_repository_iam_member (beta/available) or a resource-specific binding.
resource "google_project_iam_member" "ci_artifact_writer" {
  count   = var.ci_service_account_email != "" ? 1 : 0
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${var.ci_service_account_email}"
}