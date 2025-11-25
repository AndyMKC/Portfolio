# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ARG STORYSPARK_GCP_BQ_PROJECT_ID
ARG STORYSPARK_GCP_BQ_DATASET_ID
ARG STORYSPARK_GCP_BQ_SOURCE_TABLE_ID
ARG STORYSPARK_GCP_BQ_EMBEDDINGS_TABLE_ID

ARG MODEL_DIR=/models
ARG MODEL_NAME=all-MiniLM-L6-v2
ARG MODEL_CACHE_DIR=/root/.cache/huggingface

ENV MODEL_DIR=${MODEL_DIR}
ENV MODEL_NAME=${MODEL_NAME}
ENV EMBEDDINGS_MODEL_PATH=${MODEL_DIR}/${MODEL_NAME}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV STORYSPARK_GCP_BQ_PROJECT_ID=${STORYSPARK_GCP_BQ_PROJECT_ID}
ENV STORYSPARK_GCP_BQ_DATASET_ID=${STORYSPARK_GCP_BQ_DATASET_ID}
ENV STORYSPARK_GCP_BQ_SOURCE_TABLE_ID=${STORYSPARK_GCP_BQ_SOURCE_TABLE_ID}
ENV STORYSPARK_GCP_BQ_EMBEDDINGS_TABLE_ID=${STORYSPARK_GCP_BQ_EMBEDDINGS_TABLE_ID}
WORKDIR /src

# system deps needed for some wheels; keep minimal
RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential gcc libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# install dependencies (cacheable layer)
FROM base AS deps
COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip python -m pip install --upgrade pip setuptools wheel && pip install -r ./requirements.txt

# # Pre-download the Hugging Face model into the image.  This should run after installing requirements.txt
# # Rely on snapshot_download -- RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
# # create models dir and predownload into it
# # TODO:  Pass this in from environment variables
# RUN --mount=type=cache,target=${MODEL_CACHE_DIR} \
#     python - <<'PY'
# import os, shutil
# from huggingface_hub import snapshot_download

# MODEL_DIR = os.environ.get("MODEL_DIR")
# MODEL_NAME = os.environ.get("MODEL_NAME")
# MODEL_CACHE_DIR = os.environ.get("MODEL_CACHE_DIR")

# # download snapshot; snapshot_download returns the actual snapshot path
# snapshot_path = snapshot_download(f"sentence-transformers/{MODEL_NAME}", cache_dir=MODEL_CACHE_DIR)
# target = os.path.join(MODEL_DIR, MODEL_NAME)

# # ensure target is clean
# if os.path.exists(target):
#     shutil.rmtree(target)
# os.makedirs(target, exist_ok=True)

# # copy files, resolving symlinks to actual blob files
# for root, dirs, files in os.walk(snapshot_path):
#     rel_root = os.path.relpath(root, snapshot_path)
#     dst_root = os.path.join(target, rel_root) if rel_root != "." else target
#     os.makedirs(dst_root, exist_ok=True)
#     for name in files:
#         src = os.path.join(root, name)
#         dst = os.path.join(dst_root, name)
#         if os.path.islink(src):
#             real = os.path.realpath(src)  # absolute path to blob in cache
#             if os.path.exists(real):
#                 shutil.copy2(real, dst)
#             else:
#                 print("Missing blob for", src, "->", real)
#         else:
#             shutil.copy2(src, dst)

# print("Model placed at", target)
# PY

# make sure nobody can access it (65534 is the usual nobody uid)
RUN chown -R 65534:65534 ${MODEL_DIR} && chmod -R a+rX ${MODEL_DIR}

# copy application code
FROM base AS runtime
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
# COPY --from=deps ${MODEL_DIR} ${MODEL_DIR}
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
# 2.  docker build --progress=plain --target dev --file Dockerfile --tag qq --build-arg STORYSPARK_GCP_BQ_PROJECT_ID="storyspark-5555555" --build-arg STORYSPARK_GCP_BQ_DATASET_ID="storyspark_dataset_dev" --build-arg STORYSPARK_GCP_BQ_SOURCE_TABLE_ID="source_table_books_dev" --build-arg STORYSPARK_GCP_BQ_EMBEDDINGS_TABLE_ID="text_embeddings_books_dev" .
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