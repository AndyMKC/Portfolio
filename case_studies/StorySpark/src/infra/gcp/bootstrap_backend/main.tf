locals {
  # stable account_id prefixes must be 6-30 chars, lowercase, digits and hyphens; adjust if needed
  sa_bq_prefix  = "storyspark-bq-vertex"
  sa_run_prefix = "storyspark-cloudrun"
}

# This stack has no backend block: it creates the very bucket that every other
# stack uses for remote state, so its own state cannot live there. State is
# therefore local and discarded when the CI runner is torn down, which means
# every run starts empty and would otherwise attempt to create resources that
# already exist. These import blocks re-adopt them on each run, making the
# apply idempotent without persisting state.

import {
  to = google_storage_bucket.tfstate_bucket
  id = var.tfstate_bucket_name
}

# NOTE: import blocks do not support count/for_each, so these are unconditional.
# That means create_dev / create_prod must stay true for this stack to apply.
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

  # Single rule covering every object in the bucket, across all prefixes
  # (production state at terraform/main/infra, feature branch states at
  # terraform/<branch>/infra, and any orphaned .tflock files).
  #
  # GCS applies the earliest matching rule, so an unscoped rule plus a
  # prefix-scoped rule would let the unscoped one win and defeat the buffer.
  # A single rule keeps the behavior consistent everywhere.
  #
  # NOTE: This replaces an `age = 90` rule that was still live on the bucket.
  # `age` targets the CURRENT object, so it would have deleted live state
  # files after 90 days without an update. PR #202 intended this fix but was
  # never applied, so it is being applied here.
  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      # Only superseded (non-current) versions are eligible. The live version
      # of every object is never touched.
      days_since_noncurrent_time = 30
      # Always keep the 3 newest non-current versions as a rollback buffer,
      # even once they pass the 30 day window.
      num_newer_versions = 3
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
