// TODO:  This will be a problem if we ever have two branches active in development at the same time.  We can sort it out then.
# locals {
#   # Base name for the dataset structure
#   dataset_base_id = "book_inventory_vectors"
  
#   # The full, environment-prefixed dataset IDs
#   dataset_dev_id  = "dev_${local.dataset_base_id}"
#   dataset_prod_id = "prod_${local.dataset_base_id}"
  
#   target_dataset_id = var.git_branch == "main" ? local.dataset_prod_id : local.dataset_dev_id

#   model_base_id = "book_metadata_embedding_remote"

#   model_dev_id = "dev_${local.model_base_id}"
#   model_prod_id = "prod_${local.model_base_id}"

#   target_model_id = var.git_branch == "main" ? local.model_prod_id : local.model_dev_id

#   target_vector_dataset = var.git_branch == "main" ? google_bigquery_dataset.prod_dataset : google_bigquery_dataset.dev_dataset
# }

locals {
  # 1) Original branch name converted to lowercase so uppercase letters map to lowercase
  step_lower    = lower(var.git_branch)

  # 2) Replace any character that is not a lowercase letter, digit, or underscore with an underscore
  step_clean    = replace(local.step_lower, "/[^a-z0-9_]/", "_")

  # 3) Collapse runs of multiple underscore into a single underscore to avoid "_" sequences
  step_collapse = replace(local.step_clean, "/_{2,}/", "_")

  # 4) Trim leading and trailing underscore that may have been introduced by replacements
  step_trim     = replace(local.step_collapse, "/^_+|_+$/", "")

  # 5) Provide a fallback when the result is empty and truncate to a safe max length (100 chars)
  step_final    = length(local.step_trim) == 0 ? "unnamed" : substr(local.step_trim, 0, 100)

  # 6) Ensure the first character is a lowercase letter; if not, prefix with "s" and keep length safe
  branch_safe   = replace(local.step_final, "/^[^a-z]/", "s${substr(local.step_final, 0, 99)}")

  # 7) Environment suffix: "prod" for main branch, otherwise "dev_<branch_safe>"
  env_suffix    = var.git_branch == "main" ? "prod" : "dev_${local.branch_safe}"

  # 8) Dataset id combined with environment suffix
  dataset_id    = "${var.base_dataset_id}_${local.env_suffix}"

  # 9) Source and embeddings table ids combined with environment suffix
  source_table  = "${var.base_source_table_id}_${local.env_suffix}"
  embed_table   = "${var.base_embeddings_table_id}_${local.env_suffix}"

  # These accounts need to be provisioned by the bootstrap_backend
  is_prod             = var.git_branch == "main"
  prod_dev_env_suffix = local.is_prod ? "prod" : "dev"
  sa_bq_vertex        = "storyspark-bq-vertex-${local.prod_dev_env_suffix}"
  sa_cloudrun         = "storyspark-cloudrun-${local.prod_dev_env_suffix}"
  service_account_suffix = "${var.project_id}.iam.gserviceaccount.com"
  
  # For now, have all dev branches share the same service for convenience
  service_name        = "storyspark-service-${local.prod_dev_env_suffix}"
}

# Enable required APIs
resource "google_project_service" "bigquery" {
  project = var.project_id
  service = "bigquery.googleapis.com"
}

resource "google_project_service" "aiplatform" {
  project = var.project_id
  service = "aiplatform.googleapis.com"
}

resource "google_project_service" "run" {
  project = var.project_id
  service = "run.googleapis.com"
}

resource "google_project_service" "artifactregistry" {
  project = var.project_id
  service = "artifactregistry.googleapis.com"
}

# Artifact Registry Docker repository
resource "google_artifact_registry_repository" "docker_repo" {
  project       = var.project_id
  location      = var.region
  repository_id = var.artifact_repo_id
  format        = "DOCKER"
  description   = "Docker repo for StorySpark images"
}

resource "google_project_service" "iam" {
  project = var.project_id
  service = "iam.googleapis.com"
}

# BigQuery dataset (env-specific)
resource "google_bigquery_dataset" "embeddings" {
  project       = var.project_id
  dataset_id    = local.dataset_id
  location      = var.location
  friendly_name = "StorySpark embeddings dataset ${local.env_suffix}"
  description   = "Holds canonical book records and embeddings for ${local.env_suffix}"
}

# BigQuery source table (canonical book records)
resource "google_bigquery_table" "source_table" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.embeddings.dataset_id
  table_id   = local.source_table

  schema = jsonencode([
    { "name": "id",            "type": "STRING",    "mode": "REQUIRED" },
    { "name": "title",         "type": "STRING",    "mode": "REQUIRED" },
    { "name": "author",        "type": "STRING",    "mode": "NULLABLE" },
    { "name": "metadata_text", "type": "STRING",    "mode": "REQUIRED" },
    { "name": "last_read",     "type": "TIMESTAMP", "mode": "NULLABLE" },
    { "name": "owner_id",      "type": "STRING",    "mode": "REQUIRED" },
    { "name": "created_at",    "type": "TIMESTAMP", "mode": "REQUIRED" },
    { "name": "updated_at",    "type": "TIMESTAMP", "mode": "REQUIRED" }
  ])

  friendly_name = "StorySpark source books table ${local.env_suffix}"
  description   = "Canonical book records for StorySpark ${local.env_suffix}"

  deletion_protection = false
}

# Embeddings table to store vectors
resource "google_bigquery_table" "embeddings_table" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.embeddings.dataset_id
  table_id   = local.embed_table

  schema = jsonencode([
    { "name": "id",                   "type": "STRING",    "mode": "REQUIRED" },
    { "name": "content",              "type": "STRING",    "mode": "REQUIRED" },
    { "name": "embedding",            "type": "FLOAT64",   "mode": "REPEATED" },
    { "name": "model_id",             "type": "STRING",    "mode": "REQUIRED" },
    { "name": "embedding_created_at", "type": "TIMESTAMP", "mode": "REQUIRED" },
    { "name": "owner_id",             "type": "STRING",    "mode": "REQUIRED" }
  ])

  friendly_name = "StorySpark text embeddings ${local.env_suffix}"
  description   = "Stores text and embedding vectors for StorySpark ${local.env_suffix}"
}

# Grant dataset access to service account
resource "google_bigquery_dataset_iam_member" "sa_dataset_access" {
  dataset_id = google_bigquery_dataset.embeddings.dataset_id
  project    = var.project_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${local.sa_bq_vertex}@${local.service_account_suffix}"
}

# Grant Vertex AI usage to the service account at project scope
resource "google_project_iam_member" "sa_vertex_use" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${local.sa_bq_vertex}@${local.service_account_suffix}"
}

# Grant Cloud Run service account permission to access BigQuery
resource "google_project_iam_member" "run_sa_bq" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${local.sa_cloudrun}@${local.service_account_suffix}"
}

# Grant Cloud Run service account permission to invoke Vertex models if needed
resource "google_project_iam_member" "run_sa_vertex" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${local.sa_cloudrun}@${local.service_account_suffix}"
}

# Cloud Run service
# resource "google_cloud_run_service" "storyspark_service" {
#   name     = local.service_name
#   location = var.region
#   project  = var.project_id

#   template {
#     spec {
#       service_account_name = "${local.sa_cloudrun}@${local.service_account_suffix}"
#       containers {
#         image = var.cloud_run_image
#         ports {
#           container_port = 8080
#         }
#         env {
#           name  = "BQ_DATASET"
#           value = google_bigquery_dataset.embeddings.dataset_id
#         }
#         env {
#           name  = "SOURCE_TABLE"
#           value = google_bigquery_table.source_table.table_id
#         }
#         env {
#           name  = "EMBED_TABLE"
#           value = google_bigquery_table.embeddings_table.table_id
#         }
#         env {
#           name  = "API_KEY"
#           value = var.api_key
#         }
#         env {
#           name  = "ENV"
#           value = local.env_suffix
#         }
#       }
#     }
#   }

#   traffic {
#     percent         = 100
#     latest_revision = true
#   }
# }

# Allow unauthenticated access to Cloud Run (public endpoint)
resource "google_cloud_run_service_iam_member" "allow_unauth" {
  location = google_cloud_run_service.storyspark_service.location
  project  = var.project_id
  service  = google_cloud_run_service.storyspark_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

#
# API Gateway and Compute (Cloud Run)
# Cloud Run is the core compute, serving as both the backend and API endpoint.
#

# resource "google_artifact_registry_repository" "api_repo" {
#   project      = var.project_id
#   location     = var.region
#   repository_id = "${var.service_name}-repo"
#   description  = "Docker repository for the StorySpark API (embedding model container)"
#   format       = "DOCKER"
# }

# # A placeholder Cloud Run service definition.
# # When you deploy, you will replace 'gcr.io/cloudrun/hello' with the path
# # from the Artifact Registry: <region>-docker.pkg.dev/<project_id>/<repo_id>/<image_name>
# resource "google_cloud_run_v2_service" "api_service" {
#   name     = var.service_name
#   location = var.region

#   template {
#     # Ensure the service scales down completely when idle.
#     scaling {
#       min_instance_count = 0 
#       max_instance_count = 1 # Keep this low for testing to stay within vCPU-second limits.
#     }

#     containers {
#       # This image should contain your Python code, embedding model, and dependencies.
#       image = "us-docker.pkg.dev/cloudrun/container/hello" 

#       resources {
#         # CRITICAL FOR FREE TIER: Use the smallest config (e.g., 512MiB and 1 vCPU max)
#         # to maximize the usage under the free quota (e.g., 360k GB-seconds free).
#         cpu_idle = true # Allows CPU to be throttled when idle.
#       }
#     }
#   }

#   traffic {
#     type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
#     percent = 100
#   }

#   depends_on = [
#     google_artifact_registry_repository.api_repo
#   ]
# }

# # Allow unauthenticated access to the Cloud Run service (acts as an API Gateway)
# resource "google_cloud_run_v2_service_iam_member" "allow_public_access" {
#   provider = google-beta 

#   # The service to which the policy is being bound
#   name     = google_cloud_run_v2_service.api_service.name
#   location = var.region 

#   # Role and member for unauthenticated access
#   role     = "roles/run.invoker"
#   member   = "allUsers"
# }

# # 
# # Vector Database (Firestore in Native Mode)
# #
# resource "google_firestore_database" "default_db" {
#   project = var.project_id
#   # Name must be "(default)" for the first database
#   name     = "(default)" 
  
#   # FIX: Changed 'location' to the required attribute 'location_id'
#   location_id = var.region 
  
#   type     = "FIRESTORE_NATIVE" # Use Native Mode
  
#   # Set the desired concurrency mode. Best practice is to use OPTIMISTIC.
#   concurrency_mode = "OPTIMISTIC"
# }

# # BigQuery Dataset
# # A container for the table and ML model
# resource "google_bigquery_dataset" "dev_dataset" {
#   dataset_id                  = local.dataset_dev_id
#   friendly_name               = "Book Inventory for Dev"
#   description                 = "Books inventory per user for dev"
#   location                    = var.region
#   delete_contents_on_destroy  = true
# }

# resource "google_bigquery_dataset" "prod_dataset" {
#   dataset_id                  = local.dataset_prod_id
#   friendly_name               = "Book Inventory for Prod"
#   description                 = "Books inventory per user for prod"
#   location                    = var.region
#   delete_contents_on_destroy  = false # Set to false in production!
# }

# # BigQuery Connection (for ML Remote Model)
# # Creates a connection resource to securely access Vertex AI
# resource "google_bigquery_connection" "vertex_connection" {
#   connection_id = "vertex-ai-embed-conn"
#   location      = local.target_vector_dataset.location
#   cloud_resource {}
# }

# # BigQuery ML Remote Model (for Embeddings)
# # This model acts as a proxy to a Vertex AI model (e.g., text-embedding-004)
# resource "google_bigquery_model" "text_embedding_model" {
#   provider = google-beta.beta

#   model_id   = local.target_model_id
#   dataset_id = local.target_dataset_id
#   location   = local.target_vector_dataset.location
  
#   remote_model_info {
#     connection_id = google_bigquery_connection.vertex_connection.connection_id
#     remote_model_type = "CLOUD_AI_SERVICE_MODEL"
#     endpoint          = "text-embedding-004" # The Vertex AI embedding model
#   }
# }

# # BigQuery Table (to hold documents and embeddings)
# resource "google_bigquery_table" "embeddings_table" {
#   # This single resource block conditionally points to either the DEV or PROD dataset.
#   # Terraform will automatically identify the dependency on the chosen dataset.
#   dataset_id = local.target_dataset_id
#   table_id   = "book_metadata_embeddings"
  
#   schema = jsonencode([
#     {
#       name        = "book_id"
#       type        = "STRING"
#       mode        = "REQUIRED"
#       description = "The unique identifier for the book (Primary Key)."
#     },
#     {
#       name        = "title"
#       type        = "STRING"
#       mode        = "NULLABLE"
#       description = "The title of the book."
#     },
#     {
#       name        = "author"
#       type        = "STRING"
#       mode        = "NULLABLE"
#       description = "The author of the book."
#     },
#     {
#       name        = "owner"
#       type        = "STRING"
#       mode        = "NULLABLE"
#       description = "The owner/user who uploaded the book."
#     },
#     {
#       name        = "last_read_datetime"
#       type        = "TIMESTAMP"
#       mode        = "NULLABLE"
#       description = "The last read date and time of the book."
#     },
#     {
#       name        = "text_content"
#       type        = "STRING"
#       mode        = "NULLABLE"
#       description = "The raw text content (or chunk) used to generate the embedding."
#     },
#     {
#       # This is the vector embedding column
#       name        = "embedding_vector"
#       type        = "FLOAT"
#       mode        = "REPEATED"
#       description = "The vector embedding (Array of FLOAT64) generated by the remote model."
#     },
#   ])
# }

# # BigQuery Vector Index (for Fast Search)
# # NOTE: As of today, there is no direct `google_bigquery_vector_index` resource.
# # You must use an external tool (like a `null_resource` with `local-exec`)
# # to run the CREATE VECTOR INDEX DDL, or use a tool that supports running DDL.

# # The DDL would look like this (if running manually or via an external script):
# # CREATE OR REPLACE VECTOR INDEX my_index 
# # ON vector_search_demo_dataset.document_embeddings(embedding_vector) 
# # OPTIONS(distance_type='COSINE', index_type='IVF');