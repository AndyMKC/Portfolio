#!/usr/bin/env bash
# Convenience script for building and running StorySpark in Docker.
# Equivalent to the Makefile targets.
#
# Usage:
#   ./dev.sh dev          # build + run dev image
#   ./dev.sh dev-build    # build only
#   ./dev.sh dev-run      # run only (image already built)
#   ./dev.sh prod         # build + run prod image
#   ./dev.sh prod-build   # build only
#   ./dev.sh prod-run     # run only
#   ./dev.sh clean        # remove images
#   ./dev.sh test         # run pytest tests
#   ./dev.sh local        # run with local venv (no Docker)
#
# Override env vars on the command line:
#   ADC_PATH="/path/to/creds.json" HOST_PORT=9000 ./dev.sh dev

set -euo pipefail

# --- Configurable variables (same as Makefile) ------------------
PROJECT_ID="${PROJECT_ID:-storyspark-5555555}"
DATASET_ID="${DATASET_ID:-storyspark_dataset_dev}"
SOURCE_TABLE="${SOURCE_TABLE:-source_table_books_dev}"
EMBEDDINGS_TABLE="${EMBEDDINGS_TABLE:-text_embeddings_books_dev}"
SOURCE_MODEL_DIR="${SOURCE_MODEL_DIR:-models}"
MODEL_FILE="${MODEL_FILE:-all-MiniLM-L6-v2.onnx}"
MODEL_DATA_FILE="${MODEL_DATA_FILE:-all-MiniLM-L6-v2.onnx.data}"
MODEL_EXPORT_BUCKET_NAME="${MODEL_EXPORT_BUCKET_NAME:-model_export_bucket_volume}"
IMAGE_TAG="${IMAGE_TAG:-storyspark-dev}"
PROD_TAG="${PROD_TAG:-storyspark-prod}"
ADC_PATH="${ADC_PATH:-/c/Users/AndyM/AppData/Roaming/gcloud/application_default_credentials.json}"
HOST_PORT="${HOST_PORT:-8000}"
CONT_PORT="${CONT_PORT:-8080}"
DEBUG_PORT="${DEBUG_PORT:-5678}"
VENV_PYTHON="${VENV_PYTHON:-./venv_default/Scripts/python.exe}"

CMD="${1:-}"

# --- Functions --------------------------------------------------

dev_build() {
  echo "=== Building dev image: $IMAGE_TAG ==="
  DOCKER_BUILDKIT="${PIP_CACHE:-true}" docker build \
    --progress=plain --target dev --file Dockerfile --tag "$IMAGE_TAG" \
    --build-arg STORYSPARK_GCP_BQ_PROJECT_ID="$PROJECT_ID" \
    --build-arg STORYSPARK_GCP_BQ_DATASET_ID="$DATASET_ID" \
    --build-arg STORYSPARK_GCP_BQ_SOURCE_TABLE_ID="$SOURCE_TABLE" \
    --build-arg STORYSPARK_GCP_BQ_EMBEDDINGS_TABLE_ID="$EMBEDDINGS_TABLE" \
    --build-arg SOURCE_MODEL_DIR="$SOURCE_MODEL_DIR" \
    --build-arg MODEL_FILE="$MODEL_FILE" \
    --build-arg MODEL_DATA_FILE="$MODEL_DATA_FILE" \
    --build-arg PIP_CACHE="${PIP_CACHE:-true}" \
    --build-arg MODEL_EXPORT_BUCKET_NAME="$MODEL_EXPORT_BUCKET_NAME" \
    .
}

dev_run() {
  echo "=== Running dev container ==="
  echo "Swagger UI: http://localhost:$HOST_PORT/docs"
  echo "Debugpy:    attach to port $DEBUG_PORT in VS Code"
  docker run --rm \
    -p "$HOST_PORT:$CONT_PORT" \
    -p "$DEBUG_PORT:$DEBUG_PORT" \
    -v "$ADC_PATH":/app/adc.json:ro \
    -e GOOGLE_APPLICATION_CREDENTIALS="/app/adc.json" \
    "$IMAGE_TAG"
}

prod_build() {
  echo "=== Building prod image: $PROD_TAG ==="
  DOCKER_BUILDKIT="${PIP_CACHE:-true}" docker build \
    --file Dockerfile --target prod --tag "$PROD_TAG" \
    --build-arg STORYSPARK_GCP_BQ_PROJECT_ID="$PROJECT_ID" \
    --build-arg STORYSPARK_GCP_BQ_DATASET_ID="$DATASET_ID" \
    --build-arg STORYSPARK_GCP_BQ_SOURCE_TABLE_ID="$SOURCE_TABLE" \
    --build-arg STORYSPARK_GCP_BQ_EMBEDDINGS_TABLE_ID="$EMBEDDINGS_TABLE" \
    --build-arg MODEL_FILE="$MODEL_FILE" \
    --build-arg MODEL_DATA_FILE="$MODEL_DATA_FILE" \
    --build-arg MODEL_EXPORT_BUCKET_NAME="$MODEL_EXPORT_BUCKET_NAME" \
    .
}

prod_run() {
  echo "=== Running prod container ==="
  echo "Swagger UI: http://localhost:$HOST_PORT/docs"
  docker run --rm \
    -p "$HOST_PORT:$CONT_PORT" \
    -e GOOGLE_APPLICATION_CREDENTIALS="/app/adc.json" \
    "$PROD_TAG"
}

clean() {
  docker rmi "$IMAGE_TAG" "$PROD_TAG" 2>/dev/null || true
}

# --- Local (non-Docker) -----------------------------------------

local_run() {
    echo "=== Running app locally with venv (Swagger at http://localhost:$HOST_PORT/docs) ==="
    ./venv_default/Scripts/python.exe -m uvicorn app.main:app --host 0.0.0.0 --port "$HOST_PORT"
}

# --- Test -------------------------------------------------------

test_run() {
    echo "=== Running pytest ==="
    "$VENV_PYTHON" -m pytest tests/test_api.py -v
}

# --- Dispatch ---------------------------------------------------

case "$CMD" in
  dev)
    dev_build && dev_run
    ;;
  dev-build)
    dev_build
    ;;
  dev-run)
    dev_run
    ;;
  prod)
    prod_build && prod_run
    ;;
  prod-build)
    prod_build
    ;;
  prod-run)
    prod_run
    ;;
  clean)
    clean
    ;;
  test)
    test_run
    ;;
  local)
    local_run
    ;;
  ""|help)
    echo "Usage: ./dev.sh {dev|dev-build|dev-run|prod|prod-build|prod-run|clean|local}"
    ;;
  *)
    echo "Unknown command: $CMD"
    echo "Usage: ./dev.sh {dev|dev-build|dev-run|prod|prod-build|prod-run|clean|local}"
    exit 1
    ;;
esac
