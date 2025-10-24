locals {
  # stable account_id prefixes must be 6-30 chars, lowercase, digits and hyphens; adjust if needed
  sa_bq_prefix    = "storyspark-bq-vertex"
  sa_run_prefix   = "storyspark-cloudrun"
}

resource "google_storage_bucket" "tfstate_bucket" {
  name          = var.tfstate_bucket_name
  location      = var.region
  force_destroy = false
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  # 2. Rule for MAIN/PROD BRANCH (High Safety Buffer)
  # This targets only objects with the "main/" prefix.
  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      # Target only the main branch state file path
      matches_prefix = ["main/"]
      # Delete superseded versions older than [days_since_noncurrent_time] days...
      days_since_noncurrent_time = 30
      # ...BUT always keep the 3 newest non-current versions as a safety buffer.
      num_newer_versions = 3
    }
  }

  # Rule for ALL OTHER BRANCHES (Strict Cleanup)
  # This applies to all non-current objects, ensuring strict cleanup for feature branches.
  # For 'main/', this rule is superseded by the num_newer_versions setting
  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      # Days since the object version was superseded (became non-current)
      # Any superseded version older than [days_since_noncurrent_time] days will be deleted.
      days_since_noncurrent_time = 30
    }
  }

  # Rule to clean up ABANDONED CURRENT (LIVE) STATE FILES
  # This targets the current (live) version of *any* state file (main or feature) 
  # that hasn't been updated (creating a new version) in [age] days.
  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      # Deletes the current version if its age exceeds 90 days.
      age = 90
    }
  }
}

# Dev service accounts (created only when create_dev = true)
resource "google_service_account" "bq_vertex_dev" {
  count        = var.create_dev ? 1 : 0
  account_id   = "${local.sa_bq_prefix}-${var.dev_suffix}"   # e.g. storyspark-bq-vertex-dev
  display_name = "StorySpark BigQuery/Vertex Service Account (dev)"
  project      = var.project_id
}

resource "google_service_account" "cloudrun_dev" {
  count        = var.create_dev ? 1 : 0
  account_id   = "${local.sa_run_prefix}-${var.dev_suffix}"  # e.g. storyspark-cloudrun-dev
  display_name = "StorySpark Cloud Run Service Account (dev)"
  project      = var.project_id
}

# Prod service accounts (created only when create_prod = true)
resource "google_service_account" "bq_vertex_prod" {
  count        = var.create_prod ? 1 : 0
  account_id   = "${local.sa_bq_prefix}-${var.prod_suffix}"  # e.g. storyspark-bq-vertex-prod
  display_name = "StorySpark BigQuery/Vertex Service Account (prod)"
  project      = var.project_id
}

resource "google_service_account" "cloudrun_prod" {
  count        = var.create_prod ? 1 : 0
  account_id   = "${local.sa_run_prefix}-${var.prod_suffix}" # e.g. storyspark-cloudrun-prod
  display_name = "StorySpark Cloud Run Service Account (prod)"
  project      = var.project_id
}
