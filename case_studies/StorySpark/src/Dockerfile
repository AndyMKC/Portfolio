# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ARG STORYSPARK_GCP_BQ_PROJECT_ID
ARG STORYSPARK_GCP_BQ_DATASET_ID
ARG STORYSPARK_GCP_BQ_SOURCE_TABLE_ID
ARG STORYSPARK_GCP_BQ_EMBEDDINGS_TABLE_ID
ARG SOURCE_MODEL_DIR
ARG MODEL_FILE
ARG MODEL_DATA_FILE
# For prod (GitHub Actions), we want to not use cache since we are running out of disk space as the image is keeeping all the downloaded packges.  For local builds, we want to use cache to speed up builds.
ARG PIP_CACHE=false

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV STORYSPARK_GCP_BQ_PROJECT_ID=${STORYSPARK_GCP_BQ_PROJECT_ID}
ENV STORYSPARK_GCP_BQ_DATASET_ID=${STORYSPARK_GCP_BQ_DATASET_ID}
ENV STORYSPARK_GCP_BQ_SOURCE_TABLE_ID=${STORYSPARK_GCP_BQ_SOURCE_TABLE_ID}
ENV STORYSPARK_GCP_BQ_EMBEDDINGS_TABLE_ID=${STORYSPARK_GCP_BQ_EMBEDDINGS_TABLE_ID}
ENV STORYSPARK_IMAGE_MODEL_DIR=models
ENV STORYSPARK_MODEL_FILE=${MODEL_FILE}
ENV STORYSPARK_MODEL_DATA_FILE=${MODEL_DATA_FILE}
WORKDIR /src

# install dependencies (cacheable layer)
FROM base AS deps

# system deps needed for some wheels; keep minimal
RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential gcc libpq-dev \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip python -m pip install --upgrade pip setuptools wheel
RUN --mount=type=cache,target=/root/.cache/pip \
  if [ "$PIP_CACHE" = "true" ]; then \
    echo "**********************************************************"; \
    echo "Omitting --no-cache-dir"; \
    echo "**********************************************************"; \
    pip install -r ./requirements.txt; \
  else \
    echo "**********************************************************"; \
    echo "Using --no-cache-dir"; \
    echo "**********************************************************"; \
    pip install --no-cache-dir -r ./requirements.txt; \
  fi

# copy application code
FROM base AS runtime
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
RUN mkdir -p "${STORYSPARK_IMAGE_MODEL_DIR}"
COPY ${SOURCE_MODEL_DIR} ${STORYSPARK_IMAGE_MODEL_DIR}

# make sure nobody can access it (65534 is the usual nobody uid)
RUN chown -R 65534:65534 ${STORYSPARK_IMAGE_MODEL_DIR} && chmod -R a+rX ${STORYSPARK_IMAGE_MODEL_DIR}

COPY app ./app

# recommended production command: bind 0.0.0.0 and use port from env
ENV PORT=8080
EXPOSE 8080

# Dev stage: includes debugpy and reload
FROM runtime AS dev
RUN --mount=type=cache,target=/root/.cache/pip pip install debugpy
# Start with debugpy waiting for the VS Code attach; keep --reload for hot reload
# To debug locally:
# "qq" is my tag that I am using
# 1.  set DOCKER_BUILDKIT=1
# 2.  docker build --progress=plain --target dev --file Dockerfile --tag qq --build-arg STORYSPARK_GCP_BQ_PROJECT_ID="storyspark-5555555" --build-arg STORYSPARK_GCP_BQ_DATASET_ID="storyspark_dataset_dev" --build-arg STORYSPARK_GCP_BQ_SOURCE_TABLE_ID="source_table_books_dev" --build-arg STORYSPARK_GCP_BQ_EMBEDDINGS_TABLE_ID="text_embeddings_books_dev" --build-arg SOURCE_MODEL_DIR=models --build-arg MODEL_FILE=all-MiniLM-L6-v2.onnx --build-arg MODEL_DATA_FILE=all-MiniLM-L6-v2.onnx.data --build-arg PIP_CACHE=true .
# On Windows, we need to run gcloud auth application-default login which will launch the browser and you have to select the credentials to run as.  Then on Windows, it has issues mapping out the file path to the local credentials so we need to do a volume mount (which is the -v part below)
# 3.  docker run --rm -p 8000:8080 -p 5678:5678 -v "C:\Users\AndyM\AppData\Roaming\gcloud\application_default_credentials.json":/app/adc.json:ro -e GOOGLE_APPLICATION_CREDENTIALS="/app/adc.json" qq
# 4.  Set up the VS Code launch.json to attach to remote debug port 5678
# 5.  Launch swagger at http://localhost:8000/docs
USER nobody
CMD ["sh", "-c", "python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --ws auto --reload"]

# Prod stage: minimal runtime command for Cloud Run
FROM runtime AS prod
USER nobody
# https://storyspark-service-prod-453336860824.us-west1.run.app/docs
# 453336860824 is the Google generated unique project number
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--ws", "auto"]