terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
  required_version = ">= 1.3.0"
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Enable required GCP APIs for the later resources and terraform operations
resource "google_project_service" "enable_services" {
  for_each = toset([
    "storage.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "run.googleapis.com",
    "apigateway.googleapis.com",
    "secretmanager.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com"
  ])
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# Backend bucket for Terraform state
resource "google_storage_bucket" "tfstate" {
  name                        = var.tfstate_bucket_name
  project                     = var.project_id
  location                    = var.region
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 365
    }
  }

  labels = {
    created_by = "terraform-bootstrap"
    project    = var.project_id
  }
}

# Service account for CI / Terraform runs
resource "google_service_account" "terraform_sa" {
  account_id   = "storyspark-terraform-sa"
  display_name = "StorySpark Terraform CI service account"
  project      = var.project_id
}

# Project-level IAM binding: give the terraform service account Editor role to allow provisioning during bootstrap
resource "google_project_iam_member" "sa_editor" {
  project = var.project_id
  role    = "roles/editor"
  member  = "serviceAccount:${google_service_account.terraform_sa.email}"
}

# Optional: give storage admin so it can manage tfstate bucket (redundant with editor, but explicit)
resource "google_storage_bucket_iam_member" "tf_bucket_writer" {
  bucket = google_storage_bucket.tfstate.name
  role   = "roles/storage.admin"
  member = "serviceAccount:${google_service_account.terraform_sa.email}"
}

# Create a long-lived JSON key for the terraform service account to be used by GitHub Actions
resource "google_service_account_key" "terraform_sa_key" {
  service_account_id = google_service_account.terraform_sa.name
  public_key_type    = "TYPE_X509_PEM_FILE"
  private_key_type   = "TYPE_GOOGLE_CREDENTIALS_FILE"
}

# Outputs
output "tfstate_bucket_name" {
  value = google_storage_bucket.tfstate.name
}

output "terraform_sa_email" {
  value = google_service_account.terraform_sa.email
}

output "terraform_sa_key_json" {
  description = "Service account JSON key to store securely in GitHub Actions secrets. Mark this output as sensitive in your terminal."
  value       = google_service_account_key.terraform_sa_key.private_key
  sensitive   = true
}
