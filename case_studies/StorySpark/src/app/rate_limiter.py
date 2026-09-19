"""Rate limiting for StorySpark API.

Provides sliding-window rate limiting (in-memory or Redis-backed).
Applied to all API endpoints via HTTP middleware in app.main.create_app.

Configuration (environment variables):
    RATE_LIMIT_REQUESTS        - max requests per window (default: 100)
    RATE_LIMIT_WINDOW_SECONDS  - window size in seconds (default: 3600 = 1h)
    RATE_LIMIT_EXEMPT_PATHS    - comma-separated paths exempt from rate limiting
    REDIS_URL                  - Redis connection string (rediss://:pass@host:port)
                                 If set, uses Redis-backed limiter.
    REDIS_HOST                 - Redis host (alternative to REDIS_URL)
    REDIS_PORT                 - Redis port (default: 6379)
    REDIS_PASSWORD             - Redis password
    REDIS_USERNAME             - Redis username (default: 'default')
    REDIS_SSL                  - Use SSL (default: 'false')

Client identification:
    1. Authorization: Bearer <jwt> -> JWT 'sub' claim (no signature verification)
    2. Fallback: client IP (respects X-Forwarded-For for Cloud Run)

Note: In-memory store is per-process. For multi-instance deployments,
set REDIS_URL to use RedisRateLimiter for global limits.
"""

import os
import time
import json
import base64
import asyncio
import logging
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Optional

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None  # type: ignore

logger = logging.getLogger("app-log")


@dataclass
class RateLimitConfig:
    """Rate-limit configuration loaded from environment variables."""
    limit: int = 100
    window_seconds: int = 3600
    exempt_paths: set[str] = field(default_factory=set)

    @classmethod
    def from_env(cls) -> "RateLimitConfig":
        raw_exempt = os.environ.get("RATE_LIMIT_EXEMPT_PATHS", "")
        return cls(
            limit=int(os.environ.get("RATE_LIMIT_REQUESTS", "100")),
            window_seconds=int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "3600")),
            exempt_paths=set(p.strip() for p in raw_exempt.split(",") if p.strip()),
        )


def _extract_bearer_token(request) -> Optional[str]:
    """Return the raw bearer token from the Authorization header, or None."""
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[len("Bearer "):].strip()
    return None


def _jwt_claim(token: str, claim: str) -> Optional[str]:
    """Best-effort extraction of a JWT claim without signature verification."""
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        payload_b64 = parts[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get(claim)
    except Exception:
        return None


def get_client_identifier(request) -> str:
    """Produce a stable rate-limit key for request.

    Priority:
      1. sub claim from bearer-token JWT  -> user:<sub>
      2. email claim from bearer-token JWT -> user:<email>
      3. Client IP address                 -> ip:<address>
    """
    token = _extract_bearer_token(request)
    if token:
        sub = _jwt_claim(token, "sub")
        if sub:
            return f"user:{sub}"
        email = _jwt_claim(token, "email")
        if email:
            return f"user:{email}"

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"
    return f"ip:{ip}"


class InMemoryRateLimiter:
    """Sliding-window-log rate limiter backed by an in-memory dict.

    Thread-safe via asyncio.Lock — safe to share across concurrent tasks.
    """

    def __init__(self, config: RateLimitConfig):
        self._config = config
        self._requests: defaultdict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    @property
    def config(self) -> RateLimitConfig:
        return self._config

    async def acquire(self, client_id: str) -> tuple[bool, int, int]:
        """Record a request for client_id and determine if allowed.

        Returns (allowed, remaining, retry_after_seconds).
        """
        async with self._lock:
            now = time.monotonic()
            window_start = now - self._config.window_seconds

            bucket = self._requests[client_id]
            self._requests[client_id] = [ts for ts in bucket if ts > window_start]
            bucket = self._requests[client_id]

            if len(bucket) >= self._config.limit:
                retry_after = int(bucket[0] + self._config.window_seconds - now)
                return False, 0, max(retry_after, 1)

            bucket.append(now)
            remaining = self._config.limit - len(bucket)
            return True, remaining, 0

    def reset(self) -> None:
        """Clear all stored request timestamps. Intended for tests."""
        self._requests.clear()

    def get_state(self) -> dict:
        return {
            "limit": self._config.limit,
            "window_seconds": self._config.window_seconds,
            "exempt_paths": sorted(self._config.exempt_paths),
            "active_clients": len(self._requests),
        }


class RedisRateLimiter:
    """Redis-backed sliding-window rate limiter for distributed deployments.

    Uses Redis sorted sets to track request timestamps per client.
    """

    def __init__(self, config: RateLimitConfig, redis_client: "redis.Redis"):
        if not REDIS_AVAILABLE:
            raise RuntimeError("redis-py not installed. Install: pip install redis")
        self._config = config
        self._redis = redis_client
        self._key_prefix = "ratelimit:"

    @property
    def config(self) -> RateLimitConfig:
        return self._config

    def _make_key(self, client_id: str) -> str:
        return f"{self._key_prefix}{client_id}"

    async def acquire(self, client_id: str) -> tuple[bool, int, int]:
        key = self._make_key(client_id)
        now = time.time()
        window_start = now - self._config.window_seconds

        lua_script = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local window_start = tonumber(ARGV[2])
        local limit = tonumber(ARGV[3])
        local window_seconds = tonumber(ARGV[4])

        redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)
        local count = redis.call('ZCARD', key)

        if count >= limit then
            local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
            local retry_after = 0
            if #oldest > 0 then
                retry_after = math.ceil(oldest[2] + window_seconds - now)
                if retry_after < 1 then retry_after = 1 end
            end
            return {0, 0, retry_after}
        end

        redis.call('ZADD', key, now, now .. '-' .. math.random())
        redis.call('EXPIRE', key, window_seconds + 1)
        return {1, limit - count - 1, 0}
        """

        try:
            result = await self._redis.eval(
                lua_script, 1, key,
                str(now), str(window_start),
                str(self._config.limit),
                str(self._config.window_seconds),
            )
            return bool(result[0]), int(result[1]), int(result[2])
        except Exception as e:
            logger.error(f"Redis rate limiter error: {e}")
            return True, self._config.limit, 0

    def reset(self) -> None:
        pass

    def get_state(self) -> dict:
        return {
            "limit": self._config.limit,
            "window_seconds": self._config.window_seconds,
            "exempt_paths": sorted(self._config.exempt_paths),
            "type": "redis",
        }

    async def close(self) -> None:
        await self._redis.close()


def _create_redis_client() -> Optional["redis.Redis"]:
    """Create Redis client from env vars (REDIS_URL or REDIS_HOST/REDIS_PORT/...)."""
    if not REDIS_AVAILABLE:
        return None

    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        try:
            return redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            logger.warning(f"Failed to parse REDIS_URL: {e}")

    host = os.environ.get("REDIS_HOST")
    if not host:
        return None

    port = int(os.environ.get("REDIS_PORT", "6379"))
    password = os.environ.get("REDIS_PASSWORD")
    username = os.environ.get("REDIS_USERNAME", "default")
    ssl = os.environ.get("REDIS_SSL", "false").lower() == "true"

    try:
        return redis.Redis(
            host=host, port=port,
            username=username if username != "default" else None,
            password=password or None, ssl=ssl,
            decode_responses=True,
        )
    except Exception as e:
        logger.warning(f"Failed to create Redis client: {e}")
        return None


_rate_limiter: Optional[InMemoryRateLimiter] = None
_redis_rate_limiter: Optional[RedisRateLimiter] = None


def get_rate_limiter() -> InMemoryRateLimiter | RedisRateLimiter:
    """Return process-wide rate limiter, initializing from env if needed."""
    global _rate_limiter, _redis_rate_limiter

    redis_client = _create_redis_client()
    if redis_client:
        if _redis_rate_limiter is None:
            _redis_rate_limiter = RedisRateLimiter(RateLimitConfig.from_env(), redis_client)
        return _redis_rate_limiter

    if _rate_limiter is None:
        _rate_limiter = InMemoryRateLimiter(RateLimitConfig.from_env())
    return _rate_limiter


def init_rate_limiter(config: Optional[RateLimitConfig] = None) -> InMemoryRateLimiter | RedisRateLimiter:
    """Re-initialize the singleton rate limiter (useful for tests)."""
    global _rate_limiter, _redis_rate_limiter

    redis_client = _create_redis_client()
    if redis_client:
        if config is None:
            config = RateLimitConfig.from_env()
        _redis_rate_limiter = RedisRateLimiter(config, redis_client)
        _rate_limiter = None
        return _redis_rate_limiter

    if config is None:
        config = RateLimitConfig.from_env()
    _rate_limiter = InMemoryRateLimiter(config)
    _redis_rate_limiter = None
    return _rate_limiter
