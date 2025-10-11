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

# The backend configuration is defined in backend.tf and uses the following:
# bucket = var.tfstate_bucket_name

#
# 1 & 2. API Gateway and Compute (Cloud Run)
# Cloud Run is the core compute, serving as both the backend and API endpoint.
#
# NOTE: Cloud Run free tier includes 2M requests/month. Setting min_instance_count = 0
# ensures you pay nothing when the service is idle (scales to zero).
#
resource "google_artifact_registry_repository" "api_repo" {
  project      = var.project_id
  location     = var.region
  repository_id = "${var.service_name}-repo"
  description  = "Docker repository for the StorySpark API (embedding model container)"
  format       = "DOCKER"
}

# A placeholder Cloud Run service definition.
# When you deploy, you will replace 'gcr.io/cloudrun/hello' with the path
# from the Artifact Registry: <region>-docker.pkg.dev/<project_id>/<repo_id>/<image_name>
resource "google_cloud_run_v2_service" "api_service" {
  name     = var.service_name
  location = var.region

  template {
    # CRITICAL FOR FREE TIER: Ensure the service scales down completely when idle.
    scaling {
      min_instance_count = 0 
      max_instance_count = 1 # Keep this low for testing to stay within vCPU-second limits.
    }

    containers {
      # This image should contain your Python code, embedding model, and dependencies.
      image = "us-docker.pkg.dev/cloudrun/container/hello" 

      resources {
        # CRITICAL FOR FREE TIER: Use the smallest config (e.g., 512MiB and 1 vCPU max)
        # to maximize the usage under the free quota (e.g., 360k GB-seconds free).
        cpu_idle = true # Allows CPU to be throttled when idle.
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_artifact_registry_repository.api_repo
  ]
}

# Allow unauthenticated access to the Cloud Run service (acts as an API Gateway)
resource "google_cloud_run_v2_service_iam_member" "allow_public_access" {
  provider = google-beta 

  # The service to which the policy is being bound
  name     = google_cloud_run_v2_service.api_service.name
  location = var.region 

  # Role and member for unauthenticated access
  role     = "roles/run.invoker"
  member   = "allUsers"
}

#
# 3. Vector Database (Firestore in Native Mode)
# This is used for perpetually free document/vector storage.
#
# NOTE: The free tier includes 1 GB storage. If your vectors are large, you
# may hit this limit quickly. True vector indexing must be implemented 
# in the application layer or you must switch to a paid service later.
#
resource "google_firestore_database" "default_db" {
  project = var.project_id
  # Name must be "(default)" for the first database
  name     = "(default)" 
  
  # FIX: Changed 'location' to the required attribute 'location_id'
  location_id = var.region 
  
  type     = "FIRESTORE_NATIVE" # Use Native Mode
  
  # Set the desired concurrency mode. Best practice is to use OPTIMISTIC.
  concurrency_mode = "OPTIMISTIC"
}


#
# Outputs
#
output "api_endpoint" {
  description = "The public URL endpoint for the Cloud Run service."
  value       = google_cloud_run_v2_service.api_service.uri
}

output "artifact_registry_url" {
  description = "The full URL for the Docker Artifact Registry."
  value       = google_artifact_registry_repository.api_repo.name
}
