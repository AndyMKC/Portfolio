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
    dockerhub = {
      source  = "BarnabyShearer/dockerhub"
      version = ">= 0.0.15"
    }
    # Using google-beta is necessary for newer Cloud Run features (V2/2nd Gen)
    # google-beta = {
    #   source  = "hashicorp/google-beta"
    #   version = "~> 7.6.0"
    # }
  }
}

#
# GCP Provider Configuration
#
provider "google" {
  project = var.project_id
  region  = var.region
}

# provider "google-beta" {
#   alias   = "beta"
#   project = var.project_id
#   region  = var.region
# }

provider "dockerhub" {
  # provider configuration that supports Docker Hub PAT authentication
  # see provider docs for exact auth fields
  # Using the token even though the documentation says to not use the token (https://registry.terraform.io/providers/BarnabyShearer/dockerhub/latest/docs).  Trying to see if this works
  username = var.dockerhub_username
  password = var.dockerhub_token
}