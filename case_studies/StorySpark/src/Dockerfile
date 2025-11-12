# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# system deps needed for some wheels; keep minimal
RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential gcc libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# install dependencies (cacheable layer)
FROM base AS deps
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
  && pip install --no-cache-dir -r /app/requirements.txt

# copy application code
FROM base AS runtime
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY app /app
# ensure non-root runtime user
RUN groupadd --gid 1000 appuser \
  && useradd --uid 1000 --gid 1000 --shell /bin/false --create-home appuser \
  && chown -R appuser:appuser /app
USER appuser

# recommended production command: bind 0.0.0.0 and use port from env
ENV PORT=8080
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--loop", "uvloop", "--ws", "auto"]
