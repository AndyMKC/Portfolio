#
# Main Configuration for GCS State Bucket Creation
#

# Configure the Google Provider using the project ID variable
provider "google" {
  project = var.project_id
  region  = var.region
}

# Create the GCS bucket for storing Terraform state
resource "google_storage_bucket" "tfstate_bucket" {
  name          = var.bucket_name
  location      = var.region
  force_destroy = false # Set to true only if you need to destroy a non-empty bucket
  
  # Highly recommended: Enable versioning to keep history of your state files
  versioning {
    enabled = true
  }

  # Highly recommended: Enable uniform bucket-level access for security
  # This disables ACLs, simplifying permissions via IAM roles.
  uniform_bucket_level_access = true

  # Optional: Configure lifecycle rule to clean up older versions of state
  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      # Keep the current version and all versions less than 90 days old.
      # Only delete versions older than 90 days.
      age = 90
      with_state = "ANY"
      num_newer_versions = 1
    }
  }
}
