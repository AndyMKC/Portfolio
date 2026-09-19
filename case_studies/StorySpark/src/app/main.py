# app/main.py
import os
import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.logging_setup import setup_cloud_logging
from app.rate_limiter import get_rate_limiter, get_client_identifier

from app.books import (
    add_book_router,
    get_recommendation_router,
    mark_read_router,
    remove_book_router,
    get_all_books_router,
    clear_database_router,
    clear_and_seed_db_router
)

logger = logging.getLogger("app-log")


# ─── Shared Rate Limit Constants ──────────────────────────────────────
# Single source of truth for rate limit config used by both middleware and OpenAPI
RATE_LIMIT_CONFIG = {
    "limit": 100,
    "window_seconds": 3600,
    "exempt_paths": {"/healthz"},  # paths fully exempt from rate limiting
}

# Docs paths that are always exempt (auto-generated)
DOCS_PATHS = {"/docs", "/openapi", "/redoc"}

# 429 response headers returned by middleware and documented in OpenAPI
RATE_LIMIT_HEADERS = {
    "Retry-After": {"description": "Seconds to wait before retrying", "schema": {"type": "integer"}},
    "X-RateLimit-Limit": {"description": "Maximum number of requests per window", "schema": {"type": "integer"}},
    "X-RateLimit-Remaining": {"description": "Number of requests remaining in the window", "schema": {"type": "integer"}},
}

# 429 response body schema
RATE_LIMIT_429_RESPONSE = {
    "description": "Rate limit exceeded - too many requests",
    "headers": RATE_LIMIT_HEADERS,
}

# Base API description (used in app and OpenAPI)
BASE_DESCRIPTION = "Book recommendation and management API."

# Rate limit description used in both app description and OpenAPI info
RATE_LIMIT_DESCRIPTION = (
    f"\n\n**Rate Limiting:** All API endpoints are rate-limited to "
    f"{RATE_LIMIT_CONFIG['limit']} requests per "
    f"{RATE_LIMIT_CONFIG['window_seconds'] // 60} minutes per client. "
    "A `429 Too Many Requests` response with a "
    "`Retry-After` header is returned when the limit is exceeded."
)

APP_DESCRIPTION = BASE_DESCRIPTION + RATE_LIMIT_DESCRIPTION


def is_rate_limited_path(path: str) -> bool:
    """Check if a path should be rate limited (matches middleware logic)."""
    return path not in RATE_LIMIT_CONFIG["exempt_paths"] and not any(
        path.startswith(p) for p in DOCS_PATHS
    )


def create_app() -> FastAPI:
    app = FastAPI(
        title="StorySpark API",
        version="0.1",
        description=APP_DESCRIPTION,
    )
    app.state.cloud_logging_client = setup_cloud_logging()
    app.state.rate_limiter = get_rate_limiter()

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        rate_limiter = request.app.state.rate_limiter
        config = rate_limiter.config

        path = request.url.path
        if not is_rate_limited_path(path):
            return await call_next(request)

        client_id = get_client_identifier(request)
        allowed, remaining, retry_after = await rate_limiter.acquire(client_id)

        if not allowed:
            logger.warning(
                f"Rate limit exceeded: {client_id} "
                f"(retry_after={retry_after}s, "
                f"path={request.method} {path})"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": (
                        "Rate limit exceeded. "
                        f"Limit: {config.limit} requests per "
                        f"{config.window_seconds} seconds."
                    ),
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(config.limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(config.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        response = await call_next(request)
        user_email = getattr(request.state, "current_user_email", None)
        endpoint = request.url.path
        if user_email:
            logger.info(
                f"API call: {request.method} {endpoint} "
                f"by {user_email} -> {response.status_code}"
            )
        else:
            logger.info(
                f"API call: {request.method} {endpoint} "
                f"(unauthenticated) -> {response.status_code}"
            )
        return response

    app.include_router(add_book_router)
    app.include_router(get_recommendation_router)
    app.include_router(mark_read_router)
    app.include_router(remove_book_router)
    app.include_router(get_all_books_router)
    app.include_router(clear_database_router)
    app.include_router(clear_and_seed_db_router)

    @app.get("/healthz", tags=["health"])
    async def healthz():
        return {"status": "ok"}

    def _custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        schema = FastAPI.openapi(app)

        if "info" in schema:
            if "description" not in schema["info"]:
                schema["info"]["description"] = BASE_DESCRIPTION
            desc = schema["info"]["description"]
            if "Rate Limiting" not in desc:
                schema["info"]["description"] = desc + RATE_LIMIT_DESCRIPTION

        paths = schema.get("paths", {})
        for path, path_item in paths.items():
            if not is_rate_limited_path(path):
                continue  # skip docs paths and exempt paths
            for method_name in list(path_item.keys()):
                if not isinstance(method_name, str):
                    continue
                if method_name.lower() not in ("get", "post", "put", "patch", "delete", "head", "options", "trace"):
                    continue
                spec = path_item[method_name]
                if isinstance(spec, dict):
                    spec.setdefault("responses", {})["429"] = RATE_LIMIT_429_RESPONSE

        app.openapi_schema = schema
        return schema

    app.openapi = _custom_openapi

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
