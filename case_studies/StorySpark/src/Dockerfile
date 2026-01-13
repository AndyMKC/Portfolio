# syntax=docker/dockerfile:1
FROM python:3.11-slim-bookworm AS base

ARG STORYSPARK_GCP_BQ_PROJECT_ID
ARG STORYSPARK_GCP_BQ_DATASET_ID
ARG STORYSPARK_GCP_BQ_SOURCE_TABLE_ID
ARG STORYSPARK_GCP_BQ_EMBEDDINGS_TABLE_ID
# SOURCE_MODEL_DIR only specified by local dev builds.  For prod builds, we mount the model files as a volume mount from GCS.
ARG SOURCE_MODEL_DIR
ARG MODEL_FILE
ARG MODEL_DATA_FILE
# For prod (GitHub Actions), we want to not use cache since we are running out of disk space as the image is keeeping all the downloaded packges.  For local builds, we want to use cache to speed up builds.
ARG PIP_CACHE=false
ARG MODEL_EXPORT_BUCKET_NAME

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV STORYSPARK_GCP_BQ_PROJECT_ID=${STORYSPARK_GCP_BQ_PROJECT_ID}
ENV STORYSPARK_GCP_BQ_DATASET_ID=${STORYSPARK_GCP_BQ_DATASET_ID}
ENV STORYSPARK_GCP_BQ_SOURCE_TABLE_ID=${STORYSPARK_GCP_BQ_SOURCE_TABLE_ID}
ENV STORYSPARK_GCP_BQ_EMBEDDINGS_TABLE_ID=${STORYSPARK_GCP_BQ_EMBEDDINGS_TABLE_ID}
ENV STORYSPARK_IMAGE_MODEL_DIR=models
ENV STORYSPARK_MODEL_FILE=${MODEL_FILE}
ENV STORYSPARK_MODEL_DATA_FILE=${MODEL_DATA_FILE}
ENV STORYSPARK_MODEL_EXPORT_BUCKET_NAME=${MODEL_EXPORT_BUCKET_NAME}
WORKDIR /src

# install dependencies (cacheable layer)
FROM base AS deps

# install minimal system deps required to build wheels, install packages, then purge them
RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential gcc libpq-dev \
  && python -m pip install --upgrade pip setuptools wheel \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# install python deps using BuildKit cache (do not try to remove the mounted cache here)
RUN --mount=type=cache,target=/root/.cache/pip \
    set -eux; \
    if [ "$PIP_CACHE" = "true" ]; then \
      echo "Using pip cache"; \
      pip install -r ./requirements.txt; \
    else \
      echo "Using --no-cache-dir"; \
      pip install --no-cache-dir -r ./requirements.txt; \
    fi && \
    # Remove compiled bytecode
    find /usr/local/lib/python3.11/site-packages -name "__pycache__" -type d -exec rm -rf {} + && \
    # Remove test suites from installed packages (numpy/pandas/etc often have huge test folders)
    find /usr/local/lib/python3.11/site-packages -name "tests" -type d -exec rm -rf {} + && \
    # Remove dist-info (risky, but often safe for distroless execution if you don't use pip at runtime)
    # find /usr/local/lib/python3.11/site-packages -name "*.dist-info" -type d -exec rm -rf {} + && \
    echo "Cleanup done"

# purge build deps and clean apt caches in a separate RUN (no cache mount)
# We don't really need this step because from runtime, we only copy specific folders
# RUN set -eux; \
#     apt-get update; \
#     apt-get purge -y --auto-remove build-essential gcc libpq-dev; \
#     apt-get clean; \
#     rm -rf /var/lib/apt/lists/*

# copy application code
FROM base AS runtime
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

COPY app ./app

# recommended production command: bind 0.0.0.0 and use port from env
ENV PORT=8080
EXPOSE 8080

# Dev stage: includes debugpy and reload
FROM runtime AS dev
# We only copy the model files in the local dev target but for prod, we mount the bucket as a volume mount.
# This means we do not have to spend the space to store the model files twice (once in the cloud and once in this image)
RUN mkdir -p "${MODEL_EXPORT_BUCKET_NAME}/${STORYSPARK_IMAGE_MODEL_DIR}"
COPY ${SOURCE_MODEL_DIR} ${MODEL_EXPORT_BUCKET_NAME}/${STORYSPARK_IMAGE_MODEL_DIR}
# make sure (the user called) nobody can access it (65534 is the usual nobody uid)
RUN chown -R 65534:65534 ${MODEL_EXPORT_BUCKET_NAME}/${STORYSPARK_IMAGE_MODEL_DIR} && chmod -R a+rX ${MODEL_EXPORT_BUCKET_NAME}/${STORYSPARK_IMAGE_MODEL_DIR}
RUN --mount=type=cache,target=/root/.cache/pip pip install debugpy
# Start with debugpy waiting for the VS Code attach; keep --reload for hot reload
# To debug locally:
# "qq" is my tag that I am using
# 1.  set DOCKER_BUILDKIT=1
# 2.  docker build --progress=plain --target dev --file Dockerfile --tag qq --build-arg STORYSPARK_GCP_BQ_PROJECT_ID="storyspark-5555555" --build-arg STORYSPARK_GCP_BQ_DATASET_ID="storyspark_dataset_dev" --build-arg STORYSPARK_GCP_BQ_SOURCE_TABLE_ID="source_table_books_dev" --build-arg STORYSPARK_GCP_BQ_EMBEDDINGS_TABLE_ID="text_embeddings_books_dev" --build-arg SOURCE_MODEL_DIR=models --build-arg MODEL_FILE=all-MiniLM-L6-v2.onnx --build-arg MODEL_DATA_FILE=all-MiniLM-L6-v2.onnx.data --build-arg PIP_CACHE=true --build-arg MODEL_EXPORT_BUCKET_NAME="model_export_bucket_volume" .
# On Windows, we need to run gcloud auth application-default login which will launch the browser and you have to select the credentials to run as.  Then on Windows, it has issues mapping out the file path to the local credentials so we need to do a volume mount (which is the -v part below)
# 3.  docker run --rm -p 8000:8080 -p 5678:5678 -v "C:\Users\AndyM\AppData\Roaming\gcloud\application_default_credentials.json":/app/adc.json:ro -e GOOGLE_APPLICATION_CREDENTIALS="/app/adc.json" qq
# 4.  Set up the VS Code launch.json to attach to remote debug port 5678
# 5.  Launch swagger at http://localhost:8000/docs
USER nobody
CMD ["sh", "-c", "python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --ws auto --reload"]

# Prod stage: minimal runtime command for Cloud Run
# Use a distroless runtime for a much smaller production image.  We copy only the runtime artifacts from the runtime stage.
#FROM gcr.io/distroless/python3-debian11:nonroot AS prod
FROM gcr.io/distroless/python3-debian12:nonroot AS prod

ARG STORYSPARK_GCP_BQ_PROJECT_ID
ARG STORYSPARK_GCP_BQ_DATASET_ID
ARG STORYSPARK_GCP_BQ_SOURCE_TABLE_ID
ARG STORYSPARK_GCP_BQ_EMBEDDINGS_TABLE_ID
ARG MODEL_FILE
ARG MODEL_DATA_FILE
ARG MODEL_EXPORT_BUCKET_NAME

ENV STORYSPARK_GCP_BQ_PROJECT_ID=${STORYSPARK_GCP_BQ_PROJECT_ID}
ENV STORYSPARK_GCP_BQ_DATASET_ID=${STORYSPARK_GCP_BQ_DATASET_ID}
ENV STORYSPARK_GCP_BQ_SOURCE_TABLE_ID=${STORYSPARK_GCP_BQ_SOURCE_TABLE_ID}
ENV STORYSPARK_GCP_BQ_EMBEDDINGS_TABLE_ID=${STORYSPARK_GCP_BQ_EMBEDDINGS_TABLE_ID}
ENV STORYSPARK_IMAGE_MODEL_DIR=models
ENV STORYSPARK_MODEL_FILE=${MODEL_FILE}
ENV STORYSPARK_MODEL_DATA_FILE=${MODEL_DATA_FILE}
ENV STORYSPARK_MODEL_EXPORT_BUCKET_NAME=${MODEL_EXPORT_BUCKET_NAME}

# copy installed python packages and any executables from the runtime stage
COPY --from=runtime /usr/local /usr/local
# copy app code
COPY --from=runtime /src/app /src/app
# Model files are accessible from the volume mount.  According to Gemini, we do not need to do a chown for this like we do in the dev build
WORKDIR /src
# Ensure Python finds the packages copied to /usr/local
ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages
USER nobody

# https://storyspark-service-prod-453336860824.us-west1.run.app/docs
# 453336860824 is the Google generated unique project number
ENTRYPOINT []
CMD ["python3.11", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
