# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /src

# system deps needed for some wheels; keep minimal
RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential gcc libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# install dependencies (cacheable layer)
FROM base AS deps
COPY requirements.txt .

RUN python -m pip install --upgrade pip setuptools wheel \
  && pip install --no-cache-dir -r ./requirements.txt

# copy application code
FROM base AS runtime
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY app ./app

# recommended production command: bind 0.0.0.0 and use port from env
ENV PORT=8080
EXPOSE 8080

#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--ws", "auto"]

# Dev stage: includes debugpy and reload
FROM runtime AS dev
RUN pip install debugpy
# Start with debugpy waiting for the VS Code attach; keep --reload for hot reload
# To debug locally:
# 1.  docker build --target dev --file Dockerfile --tag <your_tag_value> .
# 2.  docker run --rm -p 8000:8080 -p 5678:5678 <your_tag_value>
# 3.  Set up the VS Code launch.json to attach to remote debug port 5678
USER nobody
CMD ["sh", "-c", "python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --ws auto --reload"]

# Prod stage: minimal runtime command for Cloud Run
FROM runtime AS prod
USER nobody
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--ws", "auto"]