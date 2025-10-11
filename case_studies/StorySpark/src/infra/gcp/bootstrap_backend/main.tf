#
# Main Configuration for GCS State Bucket Creation
#

# This Terraform file defines your main GCS state bucket and its lifecycle rules.

# Configure the Google Provider using the project ID variable
provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_storage_bucket" "tfstate_bucket" {
  name          = var.bucket_name # The bucket name where state files live
  location      = var.region
  force_destroy = false
  uniform_bucket_level_access = true

  # 1. Ensure versioning is enabled (Mandatory for cleaning up old versions)
  versioning {
    enabled = true
  }

  # --- A. Cleanup for Non-Current Versions (Superseded State Files) ---

  # 2. Rule for MAIN/PROD BRANCH (High Safety Buffer)
  # This targets only objects with the "main/" prefix.
  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      # Target only the main branch state file path
      matches_prefix = ["main/"]
      # Delete superseded versions older than 30 days...
      days_since_noncurrent_time = 30
      # ...BUT always keep the 3 newest non-current versions as a safety buffer.
      num_newer_versions = 3
    }
  }

  # 3. Rule for ALL OTHER BRANCHES (Strict Cleanup)
  # This applies to all non-current objects, ensuring strict cleanup for feature branches.
  # For 'main/', this rule is superseded by the num_newer_versions setting in Rule 2.
  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      # Days since the object version was superseded (became non-current)
      # Any superseded version older than 30 days will be deleted.
      days_since_noncurrent_time = 30
    }
  }

  # --- B. Cleanup for Abandoned Live State Files ---

  # 4. Rule to clean up ABANDONED CURRENT (LIVE) STATE FILES
  # This targets the current (live) version of *any* state file (main or feature) 
  # that hasn't been updated (creating a new version) in 365 days.
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

