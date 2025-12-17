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
  # NOTE:  Originally it was:
  # env_suffix    = var.git_branch == "main" ? "prod" : "dev_${local.branch_safe}"
  # but having it per branch does not make sense.  It actually makes sense to have one per user but I'm not spending the time to do that right now since I am the only user.
  dev_suffix  = "dev"
  prod_suffix = "prod"
  env_suffix  = var.git_branch == "main" ? "prod" : "dev"

  # 8) Dataset id combined with environment suffix
  dataset_id_dev     = "${var.base_dataset_id}_${local.dev_suffix}"
  dataset_id_prod    = "${var.base_dataset_id}_${local.prod_suffix}"

  # 9) Source and embeddings table ids combined with environment suffix
  source_table_dev   = "${var.base_source_table_id}_${local.dev_suffix}"
  source_table_prod  = "${var.base_source_table_id}_${local.prod_suffix}"
  embed_table_dev    = "${var.base_embeddings_table_id}_${local.dev_suffix}"
  embed_table_prod   = "${var.base_embeddings_table_id}_${local.prod_suffix}"

  # These accounts need to be provisioned by the bootstrap_backend
  is_prod                  = var.git_branch == "main"
  prod_dev_env_suffix      = local.is_prod ? "prod" : "dev"
  sa_bq_vertex_dev         = "storyspark-bq-vertex-${local.dev_suffix}"
  sa_bq_vertex_prod        = "storyspark-bq-vertex-${local.prod_suffix}"
  # NOTE:  I don't think for now we need a dev Cloud Run account since we are only debugging locally.  If we ever need a preview branch, then us.
  sa_cloudrun              = "storyspark-cloudrun-${local.prod_dev_env_suffix}"
  service_account_suffix   = "${var.project_id}.iam.gserviceaccount.com"
  
  # For now, have all dev branches share the same service for convenience
  service_name             = "storyspark-service-${local.prod_dev_env_suffix}"

  # Both dev and prod should share the same schema
  source_schema = jsonencode([
    { "name": "id",            "type": "STRING",    "mode": "REQUIRED" },
    { "name": "owner",         "type": "STRING",    "mode": "REQUIRED" },
    { "name": "isbn",          "type": "STRING",    "mode": "REQUIRED" },
    { "name": "title",         "type": "STRING",    "mode": "REQUIRED" },
    { "name": "author",        "type": "STRING",    "mode": "NULLABLE" },
    { "name": "last_read",     "type": "TIMESTAMP", "mode": "NULLABLE" },
    { "name": "created_at",    "type": "TIMESTAMP", "mode": "REQUIRED" }
  ])

  embeddings_schema = jsonencode([
    { "name": "isbn",                   "type": "STRING",    "mode": "REQUIRED" },
    { "name": "content",              "type": "STRING",    "mode": "REQUIRED" },
    { "name": "embeddings",            "type": "FLOAT64",   "mode": "REPEATED" },
    { "name": "model_name",             "type": "STRING",    "mode": "REQUIRED" },
    { "name": "created_at",         "type": "TIMESTAMP", "mode": "REQUIRED" },
  ])
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
  repository_id = var.artifact_docker_images_repo_id
  format        = "DOCKER"
  description   = "Docker repo for StorySpark images"

  cleanup_policy_dry_run = false

  # Policy 1: Keep only the most recent versions of specific packages
  cleanup_policies {
    id     = "keep-recent-webapp"
    action = "KEEP"
    most_recent_versions {
      keep_count            = 1
      package_name_prefixes = ["andymkc/portfolio/prod/"]
    }
  }
  
  # Policy 2: Delete everything else very quickly to save storage space
  cleanup_policies {
    id     = "delete-everything-quickly"
    action = "DELETE"
    condition {
      older_than   = "1s"
    }
  }  
}

# Artifact Registry models repository
resource "google_artifact_registry_repository" "models_repo" {
  project       = var.project_id
  location      = var.region
  repository_id = var.artifact_exported_model_repo_id
  format        = "GENERIC"
  description   = "Exported models for StorySpark"

  cleanup_policy_dry_run = false

  # Policy 1: Keep only the most recent versions of the exported model
  cleanup_policies {
    id     = "keep-recent-model"
    action = "KEEP"
    most_recent_versions {
      keep_count            = 1
    }
  }

  # Policy 2: Delete everything else very quickly to save storage space
  cleanup_policies {
    id     = "delete-everything-quickly"
    action = "DELETE"
    condition {
      older_than   = "1s"
    }
  }  
}

resource "google_project_service" "iam" {
  project = var.project_id
  service = "iam.googleapis.com"
}

# BigQuery dataset (env-specific)
resource "google_bigquery_dataset" "embeddings_dev" {
  project       = var.project_id
  dataset_id    = local.dataset_id_dev
  location      = var.location
  friendly_name = "StorySpark embeddings dataset ${local.dev_suffix}"
  description   = "Holds canonical book records and embeddings for ${local.dev_suffix}"
}
resource "google_bigquery_dataset" "embeddings_prod" {
  project       = var.project_id
  dataset_id    = local.dataset_id_prod
  location      = var.location
  friendly_name = "StorySpark embeddings dataset ${local.prod_suffix}"
  description   = "Holds canonical book records and embeddings for ${local.prod_suffix}"
}

# BigQuery source table (canonical book records)
resource "google_bigquery_table" "source_table_dev" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.embeddings_dev.dataset_id
  table_id   = local.source_table_dev

  schema = local.source_schema

  friendly_name = "StorySpark source books table ${local.dev_suffix}"
  description   = "Canonical book records for StorySpark ${local.dev_suffix}"

  deletion_protection = false
}

resource "google_bigquery_table" "source_table_prod" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.embeddings_prod.dataset_id
  table_id   = local.source_table_prod

  schema = local.source_schema

  friendly_name = "StorySpark source books table ${local.prod_suffix}"
  description   = "Canonical book records for StorySpark ${local.prod_suffix}"

  deletion_protection = false
}

# Embeddings table to store vectors
resource "google_bigquery_table" "embeddings_table_dev" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.embeddings_dev.dataset_id
  table_id   = local.embed_table_dev

  schema = local.embeddings_schema

  friendly_name = "StorySpark text embeddings ${local.dev_suffix}"
  description   = "Stores text and embedding vectors for StorySpark ${local.dev_suffix}"

  deletion_protection = false
}
resource "google_bigquery_table" "embeddings_table_prod" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.embeddings_prod.dataset_id
  table_id   = local.embed_table_prod

  schema = local.embeddings_schema

  friendly_name = "StorySpark text embeddings ${local.prod_suffix}"
  description   = "Stores text and embedding vectors for StorySpark ${local.prod_suffix}"

  deletion_protection = false
}

# Grant dataset access to service account
resource "google_bigquery_dataset_iam_member" "sa_dataset_access" {
  dataset_id = google_bigquery_dataset.embeddings_prod.dataset_id
  project    = var.project_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${local.sa_bq_vertex_prod}@${local.service_account_suffix}"
}

# Grant Vertex AI usage to the service account at project scope
resource "google_project_iam_member" "sa_vertex_use" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${local.sa_bq_vertex_prod}@${local.service_account_suffix}"
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

# # Cloud Run service
# resource "google_cloud_run_v2_service" "storyspark_service" {
#   name     = local.service_name
#   location = var.region
#   project  = var.project_id

#   template {
#     # REQUIRED: Enable the Second Generation Execution Environment for future GCS volume mounts
#     execution_environment = "EXECUTION_ENVIRONMENT_GEN2"

#     # Service account is now directly under 'template' in V2
#     service_account = "${local.sa_cloudrun}@${local.service_account_suffix}"
    
#     containers {
#       image = var.cloud_run_image
      
#       resources {
#         # Using the simplified V2 resource limits block
#         limits = {
#           memory = "1Gi"
#         }
#       }
      
#       ports {
#         container_port = 8080
#       }
      
#       # --- GCS VOLUME MOUNT CONFIGURATION (Currently Commented Out) ---
#       /*
#       volume_mounts {
#         name       = "model-bucket-volume"
#         mount_path = "/models_gcs"
#       }
      
#       env {
#         name  = "STORYSPARK_IMAGE_MODEL_DIR"
#         value = "/models_gcs"
#       }
#       */
#       # --- END GCS VOLUME MOUNT CONFIGURATION ---

#       # Existing Env Vars (Keep these as they point to your BigQuery setup)
#       env {
#         name  = "BQ_DATASET"
#         value = google_bigquery_dataset.embeddings_prod.dataset_id
#       }
#       env {
#         name  = "SOURCE_TABLE"
#         value = google_bigquery_table.source_table_prod.table_id
#       }
#       env {
#         name  = "EMBED_TABLE"
#         value = google_bigquery_table.embeddings_table_prod.table_id
#       }
#       env {
#         name  = "API_KEY"
#         value = var.api_key
#       }
#       env {
#         name  = "ENV"
#         value = local.env_suffix
#       }
#     }
    
#     # --- V2 VOLUME DEFINITION (Currently Commented Out) ---
#     /*
#     volumes {
#       name = "model-bucket-volume"
#       gcs {
#         bucket    = "YOUR_MODEL_BUCKET_NAME" 
#         read_only = true
#       }
#     }
#     */
#     # --- END V2 VOLUME DEFINITION ---
#   }

#   # V2 Traffic definition
#   traffic {
#     type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
#     percent = 100
#   }
# }

# # Allow unauthenticated access to Cloud Run (public endpoint)
# resource "google_cloud_run_v2_service_iam_member" "allow_unauth" {
#   location = google_cloud_run_v2_service.storyspark_service.location
#   project  = var.project_id
#   name     = google_cloud_run_v2_service.storyspark_service.name
#   role     = "roles/run.invoker"
#   member   = "allUsers"
# }

# # Cloud Run service
# resource "google_cloud_run_service" "storyspark_service" {
#   provider = google-beta
#   name     = local.service_name
#   location = var.region
#   project  = var.project_id

#   template {
#     spec {
#       service_account_name = "${local.sa_cloudrun}@${local.service_account_suffix}"
#       containers {
#         image = var.cloud_run_image
#         resources {
#           limits= {
#             cpu    = "1000m"
#             memory = "1Gi" # Docker image with the embeddings model seems to increase the memory footprint to be 542 which is above the default 512.
#           }
#         }

#         ports {
#           container_port = 8080
#         }

#         env {
#           name  = "BQ_DATASET"
#           value = google_bigquery_dataset.embeddings_prod.dataset_id
#         }

#         env {
#           name  = "SOURCE_TABLE"
#           value = google_bigquery_table.source_table_prod.table_id
#         }

#         env {
#           name  = "EMBED_TABLE"
#           value = google_bigquery_table.embeddings_table_prod.table_id
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



# # Allow unauthenticated access to Cloud Run (public endpoint)

# resource "google_cloud_run_service_iam_member" "allow_unauth" {
#   provider = google-beta
#   location = google_cloud_run_service.storyspark_service.location
#   project  = var.project_id
#   service  = google_cloud_run_service.storyspark_service.name
#   role     = "roles/run.invoker"
#   member   = "allUsers"
# }
