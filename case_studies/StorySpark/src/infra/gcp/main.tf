locals {
  # Base name for the dataset structure
  dataset_base_id = "book_inventory_vectors"
  
  # The full, environment-prefixed dataset IDs
  dataset_dev_id  = "dev_${local.dataset_base_id}"
  dataset_prod_id = "prod_${local.dataset_base_id}"
  
  target_dataset_id = var.git_branch == "main" ? local.dataset_prod_id : local.dataset_dev_id
}

#
# API Gateway and Compute (Cloud Run)
# Cloud Run is the core compute, serving as both the backend and API endpoint.
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
    # Ensure the service scales down completely when idle.
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
# Vector Database (Firestore in Native Mode)
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

# BigQuery Dataset
# A container for the table and ML model
resource "google_bigquery_dataset" "vector_dataset" {
  dataset_id                  = var.dataset_id
  friendly_name               = "Book Inventory"
  description                 = "Books inventory per user"
  location                    = var.region
  delete_contents_on_destroy  = false # Set to false in production!
}

resource "google_bigquery_dataset" "dev_dataset" {
  dataset_id                  = local.dataset_dev_id
  friendly_name               = "Book Inventory for Dev"
  description                 = "Books inventory per user for dev"
  location                    = var.region
  delete_contents_on_destroy  = true
}

resource "google_bigquery_dataset" "prod_dataset" {
  dataset_id = local.dataset_prod_id
  friendly_name               = "Book Inventory for Prod"
  description                 = "Books inventory per user for prod"
  location                    = var.region
  delete_contents_on_destroy  = false # Set to false in production!
}

# BigQuery Connection (for ML Remote Model)
# Creates a connection resource to securely access Vertex AI
resource "google_bigquery_connection" "vertex_connection" {
  connection_id = "vertex-ai-embed-conn"
  location      = google_bigquery_dataset.vector_dataset.location
  cloud_resource {}
}

# BigQuery ML Remote Model (for Embeddings)
# This model acts as a proxy to a Vertex AI model (e.g., text-embedding-004)
resource "google_bigquery_model" "text_embedding_model" {
  model_id   = "book_metadata_embedding_remote"
  dataset_id = local.target_dataset_id
  location   = google_bigquery_dataset.vector_dataset.location
  
  remote_model_info {
    connection_id = google_bigquery_connection.vertex_connection.connection_id
    remote_model_type = "CLOUD_AI_SERVICE_MODEL"
    endpoint          = "text-embedding-004" # The Vertex AI embedding model
  }
}

# BigQuery Table (to hold documents and embeddings)
resource "google_bigquery_table" "embeddings_table" {
  # This single resource block conditionally points to either the DEV or PROD dataset.
  # Terraform will automatically identify the dependency on the chosen dataset.
  dataset_id = local.target_dataset_id
  table_id   = "book_metadata_embeddings"
  
  schema = jsonencode([
    {
      name        = "book_id"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "The unique identifier for the book (Primary Key)."
    },
    {
      name        = "title"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "The title of the book."
    },
    {
      name        = "author"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "The author of the book."
    },
    {
      name        = "owner"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "The owner/user who uploaded the book."
    },
    {
      name        = "last_read_datetime"
      type        = "TIMESTAMP"
      mode        = "NULLABLE"
      description = "The last read date and time of the book."
    },
    {
      name        = "text_content"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "The raw text content (or chunk) used to generate the embedding."
    },
    {
      # This is the vector embedding column
      name        = "embedding_vector"
      type        = "FLOAT"
      mode        = "REPEATED"
      description = "The vector embedding (Array of FLOAT64) generated by the remote model."
    },
  ])
}

# BigQuery Vector Index (for Fast Search)
# NOTE: As of today, there is no direct `google_bigquery_vector_index` resource.
# You must use an external tool (like a `null_resource` with `local-exec`)
# to run the CREATE VECTOR INDEX DDL, or use a tool that supports running DDL.

# The DDL would look like this (if running manually or via an external script):
# CREATE OR REPLACE VECTOR INDEX my_index 
# ON vector_search_demo_dataset.document_embeddings(embedding_vector) 
# OPTIONS(distance_type='COSINE', index_type='IVF');