# Redis Cloud Infrastructure

This Terraform configuration sets up a **Redis Cloud** database using the
perpetually free tier plan. The database is used for distributed rate limiting
across multiple application instances (instead of in-memory rate limiting).

## Prerequisites

1. A [Redis Cloud](https://redis.io) account with API access enabled.
2. Redis Cloud API credentials (both **API Key** and **API Secret**).
   - These are different from the Redis database password.
   - The API Key is public; the API Secret is private.

## Required GitHub Secrets/Variables

| Name                   | Type   | Description                                     |
|------------------------|--------|-------------------------------------------------|
| `REDIS_API_KEY`         | Variable | Redis Cloud API Key (public)                  |
| `REDIS_API_SECRET`      | Secret   | Redis Cloud API Secret (private)              |
| `REDIS_DATABASE_NAME`   | Variable | Redis database name (default: `storyspark-redis`) |
| `REDIS_CLOUD_PROVIDER`  | Variable | Cloud provider: `GCP`, `AWS`, or `AZURE` (default: `GCP`) |
| `REDIS_REGION`          | Variable | Cloud region (default: `us-west1`)             |
| `REDIS_PLAN_SIZE_MB` | Variable | Free tier size in MB (default: `30`)          |

> **⚠️ Note:** Redis Cloud requires BOTH an API Key and an API Secret.
> The API Key is the public key shown in the Redis Cloud console under
> **Access Management** → **API Keys**. The API Secret is the private
> key that accompanies it. If you only have one, you may need to
> generate a new key pair in the Redis Cloud console.

### Getting Redis Cloud API Credentials

1. Go to [Redis Cloud Console](https://redis.com/redis-enterprise-cloud/) → your dashboard
2. **Access Management** → **API Keys** tab
3. Click **Create API Key** or use an existing one
4. Copy the **API Key** (public) → Add as GitHub **Variable** `REDIS_API_KEY`
5. Copy the **API Secret** (private) → Add as GitHub **Secret** `REDIS_API_SECRET`

> **Note:** These credentials are **permanently free tier enabled** when used with
> the Essentials subscription type. No billing will occur for the 30MB free tier.

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

Deployment is automated via the GitHub Actions workflow at
`.github/workflows/deploy_storyspark.yml` (root-level monorepo workflow), which:

1. Triggers on push to `main` or manual dispatch (`workflow_dispatch`)
2. Sets up Terraform and authenticates to GCP via OIDC
3. Passes `REDIS_API_KEY` (GitHub **variable**) and `REDIS_API_SECRET`
   (GitHub **secret**) to Terraform as `TF_VAR_` environment variables,
   which map to `var.rediscloud_api_key` and `var.rediscloud_api_secret`
4. Runs `terraform init`, `terraform plan`, and `terraform apply`

```bash
cd src/infra/gcp/main
terraform init \
  -backend-config="bucket=storyspark-tf-state" \
  -backend-config="prefix=terraform/state" \
  -reconfigure
terraform plan \
  -var="project_id=YOUR_PROJECT_ID" \
  -var="region=us-west1" \
  -var="redis_database_name=storyspark-redis" \
  -var="redis_cloud_provider=GCP" \
  -var="redis_region=us-west1" \
  -var="redis_free_plan_size_mb=${{ env.REDIS_PLAN_SIZE_MB }}" \
terraform apply \
  -var="project_id=YOUR_PROJECT_ID" \
  -var="region=us-west1" \
  -var="redis_database_name=storyspark-redis" \
  -var="redis_cloud_provider=GCP" \
  -var="redis_region=us-west1" \
    -var="redis_free_plan_size_mb=${{ env.REDIS_PLAN_SIZE_MB }}" \
  -auto-approve
```

For manual deployments, ensure the API credentials are available as environment variables:

```bash
export TF_VAR_rediscloud_api_key="$REDIS_API_KEY"
export TF_VAR_rediscloud_api_secret="$REDIS_API_SECRET"
terraform -chdir=src/infra/gcp/main apply
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