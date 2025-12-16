terraform {
  required_version = ">= 1.2.0"

  # The GCS backend configuration is left empty here.
  # The bucket name and prefix will be injected via the 
  # 'init' command in GitHub Actions using -backend-config.
  backend "gcs" {}

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.6.0"
    }

    # Using google-beta is necessary for newer Cloud Run features (V2/2nd Gen)
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 7.6.0"
    }

    dockerhub = {
      source  = "barnabyshearer/dockerhub"
      version = ">= 0.0.1"
    }
  }
}

#
# GCP Provider Configuration
#
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}
