# Redis Cloud Infrastructure

This Terraform configuration sets up a **Redis Cloud** database using the
perpetually free tier plan. The database is used for distributed rate limiting
across multiple application instances (instead of in-memory rate limiting).

## Prerequisites

1. A [Redis Cloud](https://redis.io) account with API access enabled.
2. Redis Cloud API credentials (both **API Key** and **API Secret**).
   - These are different from the Redis database password.
   - The API Key is public; the API Secret is private.

## Required GitHub Secrets

| Secret Name        | Description                         |
|--------------------|-------------------------------------|
| `REDIS_API_KEY`     | Redis Cloud API Key (public)        |
| `REDIS_API_SECRET`  | Redis Cloud API Secret (private)    |

> **⚠️ Note:** Redis Cloud requires BOTH an API Key and an API Secret.
> The API Key is the public key shown in the Redis Cloud console under
> **Data Access > General**. The API Secret is the private key that
> accompanies it. If you only have one, you may need to generate a new
> key pair in the Redis Cloud console.

## Usage

### Standalone (independent Redis setup)

```bash
cd src/infra/redis
terraform init
terraform plan -var="rediscloud_api_key=$REDIS_API_KEY" -var="rediscloud_api_secret=$REDIS_API_SECRET"
terraform apply -var="rediscloud_api_key=$REDIS_API_KEY" -var="rediscloud_api_secret=$REDIS_API_SECRET"
```

### As part of the GCP infrastructure

The `src/infra/gcp/main` Terraform configuration also includes the Redis
database resource. This is the recommended approach since it allows the Cloud Run
service to reference the Redis database directly for environment variable
injection.

```bash
cd src/infra/gcp/main
terraform init
terraform plan \
  -var="project_id=YOUR_PROJECT_ID" \
  -var="region=us-west1" \
  -var="rediscloud_api_key=$REDIS_API_KEY" \
  -var="rediscloud_api_secret=$REDIS_API_SECRET"
terraform apply \
  -var="project_id=YOUR_PROJECT_ID" \
  -var="region=us-west1" \
  -var="rediscloud_api_key=$REDIS_API_KEY" \
  -var="rediscloud_api_secret=$REDIS_API_SECRET"
```

## Free Tier Details

The Redis Cloud free tier includes:
- **30 MB** of storage
- **1** database
- **No** read replicas
- **Redis** protocol only (not OSS cluster)
- Select regions on AWS, GCP, and Azure

## Application Configuration

When running the app with Redis, set these environment variables:

- `REDIS_URL`: Full connection string (e.g., `rediss://:password@host:port`)
  OR
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `REDIS_USERNAME`, `REDIS_SSL`: Individual connection parameters

The application automatically detects Redis configuration and uses the
`RedisRateLimiter` instead of `InMemoryRateLimiter`.

## Outputs

| Output                | Description                                  |
|-----------------------|----------------------------------------------|
| `database_id`         | Redis database ID                            |
| `database_endpoint`   | Redis endpoint (host)                        |
| `database_port`       | Redis port                                   |
| `database_name`       | Name of the database                         |
| `database_status`     | Status (active, pending)                     |
| `redis_connection_string` | Full connection string (`rediss://:...`) |
| `redis_host`          | Redis host                                   |
| `redis_port`          | Redis port                                   |
| `redis_username`      | Redis username (default: "default")          |
| `redis_password`      | Redis password (sensitive)                   |