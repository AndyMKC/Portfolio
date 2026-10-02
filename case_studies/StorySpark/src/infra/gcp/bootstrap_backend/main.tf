locals {
  # stable account_id prefixes must be 6-30 chars, lowercase, digits and hyphens; adjust if needed
  sa_bq_prefix  = "storyspark-bq-vertex"
  sa_run_prefix = "storyspark-cloudrun"
}

# Import existing resources on first run (idempotent)
import {
  to = google_storage_bucket.tfstate_bucket
  id = var.tfstate_bucket_name
}

import {
  to = google_service_account.bq_vertex_dev[0]
  id = "projects/${var.project_id}/serviceAccounts/${local.sa_bq_prefix}-${var.dev_suffix}@${var.project_id}.iam.gserviceaccount.com"
}

import {
  to = google_service_account.cloudrun_dev[0]
  id = "projects/${var.project_id}/serviceAccounts/${local.sa_run_prefix}-${var.dev_suffix}@${var.project_id}.iam.gserviceaccount.com"
}

import {
  to = google_service_account.bq_vertex_prod[0]
  id = "projects/${var.project_id}/serviceAccounts/${local.sa_bq_prefix}-${var.prod_suffix}@${var.project_id}.iam.gserviceaccount.com"
}

import {
  to = google_service_account.cloudrun_prod[0]
  id = "projects/${var.project_id}/serviceAccounts/${local.sa_run_prefix}-${var.prod_suffix}@${var.project_id}.iam.gserviceaccount.com"
}

resource "google_storage_bucket" "tfstate_bucket" {
  name                        = var.tfstate_bucket_name
  location                    = var.region
  force_destroy               = false
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

  # Rule to clean up OLD NON-CURRENT VERSIONS only
  # Keeps the current (live) version forever, only deletes superseded versions
  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      # Delete non-current versions older than 90 days
      days_since_noncurrent_time = 90
    }
  }
}

# NOTE:  On further reflection, we may not need the dev accounts because the plan never gets applied except in main
# and the only people that need to interact with the dev environment are humans using their own accounts.
# For now, we'll keep it here but we can remove it later if desired.
# Dev service accounts (created only when create_dev = true)
resource "google_service_account" "bq_vertex_dev" {
  count        = var.create_dev ? 1 : 0
  account_id   = "${local.sa_bq_prefix}-${var.dev_suffix}" # e.g. storyspark-bq-vertex-dev
  display_name = "StorySpark BigQuery/Vertex Service Account (dev)"
  project      = var.project_id
}

resource "google_service_account" "cloudrun_dev" {
  count        = var.create_dev ? 1 : 0
  account_id   = "${local.sa_run_prefix}-${var.dev_suffix}" # e.g. storyspark-cloudrun-dev
  display_name = "StorySpark Cloud Run Service Account (dev)"
  project      = var.project_id
}

# Prod service accounts (created only when create_prod = true)
resource "google_service_account" "bq_vertex_prod" {
  count        = var.create_prod ? 1 : 0
  account_id   = "${local.sa_bq_prefix}-${var.prod_suffix}" # e.g. storyspark-bq-vertex-prod
  display_name = "StorySpark BigQuery/Vertex Service Account (prod)"
  project      = var.project_id
}

resource "google_service_account" "cloudrun_prod" {
  count        = var.create_prod ? 1 : 0
  account_id   = "${local.sa_run_prefix}-${var.prod_suffix}" # e.g. storyspark-cloudrun-prod
  display_name = "StorySpark Cloud Run Service Account (prod)"
  project      = var.project_id
}
