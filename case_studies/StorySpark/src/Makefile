# Makefile   local dev convenience targets (extracted from Dockerfile comments)
#
# Usage:
#   make dev          # build the dev image and run it
#   make dev-build    # build only
#   make dev-run      # run only (assumes image is already built)
#   make prod         # build and run the prod (distroless) image
#   make clean        # remove built images
#
# Override any of the variables below on the command line, e.g.:
#   make dev ADC_PATH="/home/user/.config/gcloud/application_default_credentials.json" \
#              PROJECT_ID="my-prod-project"

# --- Configurable variables -------------------------------------
PROJECT_ID       ?= storyspark-5555555
DATASET_ID       ?= storyspark_dataset_dev
SOURCE_TABLE     ?= source_table_books_dev
EMBEDDINGS_TABLE ?= text_embeddings_books_dev
SOURCE_MODEL_DIR  ?= models
MODEL_FILE        ?= all-MiniLM-L6-v2.onnx
MODEL_DATA_FILE   ?= all-MiniLM-L6-v2.onnx.data
MODEL_EXPORT_BUCKET_NAME ?= model_export_bucket_volume
IMAGE_TAG  ?= storyspark-dev
PROD_TAG   ?= storyspark-prod
# Detect default credentials location
# Try to auto-detect but allow override: make dev ADC_PATH="/path/to/credentials.json"
ifeq ($(OS),Windows_NT)
	# Windows - use PowerShell to get USERPROFILE
	USER_HOME := $(shell powershell -Command "$$env:USERPROFILE")
else
	USER_HOME := $(HOME)
endif
ADC_PATH ?= $(USER_HOME)/.config/gcloud/application_default_credentials.json
HOST_PORT  ?= 8000
CONT_PORT  ?= 8080
DEBUG_PORT ?= 5678
VENV_PYTHON ?= ./venv_default/Scripts/python.exe
PIP_CACHE ?= true

# --- Targets ----------------------------------------------------

.PHONY: dev dev-build dev-run prod prod-build prod-run clean local help

test: ## Run pytest tests
	$(VENV_PYTHON) -m pytest tests/test_api.py -v

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m               \033[0m \n", $$1, $$2}'

dev: dev-build dev-run ## Build and run the dev container

dev-build: ## Build the dev (debugpy + hot-reload) image
	DOCKER_BUILDKIT=$(PIP_CACHE) docker build \
		--progress=plain --target dev --file Dockerfile --tag $(IMAGE_TAG) \
		--build-arg STORYSPARK_GCP_BQ_PROJECT_ID="$(PROJECT_ID)" \
		--build-arg STORYSPARK_GCP_BQ_DATASET_ID="$(DATASET_ID)" \
		--build-arg STORYSPARK_GCP_BQ_SOURCE_TABLE_ID="$(SOURCE_TABLE)" \
		--build-arg STORYSPARK_GCP_BQ_EMBEDDINGS_TABLE_ID="$(EMBEDDINGS_TABLE)" \
		--build-arg SOURCE_MODEL_DIR="$(SOURCE_MODEL_DIR)" \
		--build-arg MODEL_FILE="$(MODEL_FILE)" \
		--build-arg MODEL_DATA_FILE="$(MODEL_DATA_FILE)" \
		--build-arg PIP_CACHE=$(PIP_CACHE) \
		--build-arg MODEL_EXPORT_BUCKET_NAME="$(MODEL_EXPORT_BUCKET_NAME)" \
		.

dev-run: ## Run the dev container (Swagger at http://localhost:$(HOST_PORT)/docs)
	@echo "Starting dev container - server will wait for debugger on port 5678..."
ifeq ($(OS),Windows_NT)
	@powershell -Command "docker run --rm -p $(HOST_PORT):$(CONT_PORT) -p $(DEBUG_PORT):$(DEBUG_PORT) -v '$(ADC_PATH):/app/adc.json:ro' -e GOOGLE_APPLICATION_CREDENTIALS='/app/adc.json' $(IMAGE_TAG)"
else
	@docker run --rm -p $(HOST_PORT):$(CONT_PORT) -p $(DEBUG_PORT):$(DEBUG_PORT) -v $(ADC_PATH):/app/adc.json:ro -e GOOGLE_APPLICATION_CREDENTIALS=/app/adc.json $(IMAGE_TAG)
endif

prod: prod-build prod-run ## Build and run the prod (distroless) image

prod-build: ## Build the prod image
	DOCKER_BUILDKIT=$(PIP_CACHE) docker build \
		--file Dockerfile --target prod --tag $(PROD_TAG) \
		--build-arg STORYSPARK_GCP_BQ_PROJECT_ID="$(PROJECT_ID)" \
		--build-arg STORYSPARK_GCP_BQ_DATASET_ID="$(DATASET_ID)" \
		--build-arg STORYSPARK_GCP_BQ_SOURCE_TABLE_ID="$(SOURCE_TABLE)" \
		--build-arg STORYSPARK_GCP_BQ_EMBEDDINGS_TABLE_ID="$(EMBEDDINGS_TABLE)" \
		--build-arg MODEL_FILE="$(MODEL_FILE)" \
		--build-arg MODEL_DATA_FILE="$(MODEL_DATA_FILE)" \
		--build-arg MODEL_EXPORT_BUCKET_NAME="$(MODEL_EXPORT_BUCKET_NAME)" \
		.

prod-run: ## Run the prod container
	docker run --rm \
		-p $(HOST_PORT):$(CONT_PORT) \
		-e GOOGLE_APPLICATION_CREDENTIALS="/app/adc.json" \
		$(PROD_TAG)

clean: ## Remove built Docker images
	-docker rmi $(IMAGE_TAG) $(PROD_TAG) 2>/dev/null || true

# --- Local (non-Docker) development ------------------------------
# Uses the existing venv at venv_default/
VENV_PYTHON ?= ./venv_default/Scripts/python.exe

local: ## Run the app locally with venv (no Docker) -- Swagger at http://localhost:$(HOST_PORT)/docs
	$(VENV_PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port $(HOST_PORT)
