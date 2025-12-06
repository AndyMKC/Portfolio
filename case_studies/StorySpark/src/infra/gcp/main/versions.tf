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
    # # Barnaby
    # dockerhub = {
    #   source  = "BarnabyShearer/dockerhub"
    #   version = ">= 0.0.15"
    # }
    docker = {
      source  = "docker/docker"
      version = "~> 0.2"
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

# Barnaby
# provider "dockerhub" {
#   # Using password instead of token because that's what the documentation demands -- https://registry.terraform.io/providers/BarnabyShearer/dockerhub/latest/docs
#   username = var.dockerhub_username
#   password = var.dockerhub_password
#   #password = var.dockerhub_token
# }

provider "docker" {
  # https://github.com/docker/terraform-provider-docker
  username = var.dockerhub_username
  password = var.dockerhub_password
  #password = var.dockerhub_token
}