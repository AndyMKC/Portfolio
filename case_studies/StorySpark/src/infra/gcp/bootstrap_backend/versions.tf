#
# Terraform and Provider Version Constraints
#

terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      # Changing to ~> 7.0 allows all versions >= 7.0 and < 8.0, accommodating 7.5.0.
      version = "~> 7.0"
    }
  }
}
