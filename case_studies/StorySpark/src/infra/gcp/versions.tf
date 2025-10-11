terraform {
  # The GCS backend configuration is left empty here.
  # The bucket name and prefix will be injected via the 
  # 'init' command in GitHub Actions using -backend-config.
  backend "gcs" {}

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    # Using google-beta is necessary for newer Cloud Run features (V2/2nd Gen)
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
}