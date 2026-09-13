"""
Rate limiting for StorySpark API.

Provides an in-memory sliding-window rate limiter that enforces a
maximum number of API requests per client within a configurable time
window.  The limiter is applied to every Swagger-documented endpoint via
HTTP middleware (see ``app.main.create_app``).

Configuration (environment variables):

    RATE_LIMIT_REQUESTS        – max requests per window (default: 100)
    RATE_LIMIT_WINDOW_SECONDS  – window size in seconds (default: 3600 = 1 h)
        RATE_LIMIT_EXEMPT_PATHS    – comma-separated paths exempt from
                                  rate limiting
    REDIS_URL                  – Redis connection string (e.g. rediss://:password@host:port)
                                 If set, uses Redis-backed rate limiter instead of in-memory.
    REDIS_HOST                 - Redis host (alternative to REDIS_URL)
    REDIS_PORT                 - Redis port (default: 6379)
    REDIS_PASSWORD             - Redis password
    REDIS_USERNAME             - Redis username (default: 'default')
    REDIS_SSL                  - Use SSL for Redis connection (default: 'false')

Client identification
---------------------

    1. If an ``Authorization: Bearer <jwt>`` header is present, the JWT
       payload is decoded **without** signature verification.  The ``sub``
       claim is used as the key, giving per-user rate limiting for
       authenticated requests.  Actual token validation still happens
       later in ``app.auth.get_current_user``.
    2. If no bearer token is present (or it can't be parsed), the
       client's IP address is used instead (respecting ``X-Forwarded-For``
       for Cloud Run / reverse-proxy setups).

.. note::

    The in-memory store is **per-process**.  For multi-instance
    deployments (e.g. scaled Cloud Run services), each instance enforces
    its own independent limit.  To enforce a *global* limit across
    instances, replace :class:`InMemoryRateLimiter` with a Redis-backed
    implementation — set the ``REDIS_URL`` environment variable to enable
    the :class:`RedisRateLimiter` which uses Redis sorted sets for a
    distributed sliding window.  The ``acquire`` method signature stays the same.
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


# ── Configuration ──────────────────────────────────────────────────────


@dataclass
class RateLimitConfig:
    """Rate-limit configuration loaded from environment variables."""

    limit: int = 100
    window_seconds: int = 3600  # 1 hour
    exempt_paths: set[str] = field(
        default_factory=set,
    )

    @classmethod
    def from_env(cls) -> "RateLimitConfig":
        """Build a config from environment variables.

        This allows operators to change the rate limit without code changes:

            RATE_LIMIT_REQUESTS=50 RATE_LIMIT_WINDOW_SECONDS=1800 python ...

        """
                raw_exempt = os.environ.get(
            "RATE_LIMIT_EXEMPT_PATHS", ""
        )
        return cls(
            limit=int(os.environ.get("RATE_LIMIT_REQUESTS", "100")),
            window_seconds=int(
                os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "3600")
            ),
            exempt_paths=set(
                p.strip() for p in raw_exempt.split(",") if p.strip()
            ),
        )


# ── Client identification ──────────────────────────────────────────────


def _extract_bearer_token(request) -> Optional[str]:
    """Return the raw bearer token from the Authorization header, or None."""
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[len("Bearer "):].strip()
    return None


def _jwt_claim(token: str, claim: str) -> Optional[str]:
    """
    Best-effort extraction of a JWT claim **without** signature verification.

    The actual token validation still happens later in
    :func:`app.auth.get_current_user` — this is purely to produce a stable
    client key so that the same user is consistently rate-limited.
    """
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        payload_b64 = parts[1]
        # JWT uses URL-safe base64 without padding
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get(claim)
    except Exception:
        return None


def get_client_identifier(request) -> str:
    """
    Produce a stable rate-limit key for *request*.

    Priority:

      1. ``sub`` claim from the bearer-token JWT  -> ``user:<sub>``
      2. ``email`` claim from the bearer-token JWT -> ``user:<email>``
      3. Client IP address                         -> ``ip:<address>``

    The ``sub`` (subject) claim is preferred because it is stable across
    token refreshes, whereas the ``email`` claim could change if the
    user's email address changes.
    """
    token = _extract_bearer_token(request)
    if token:
        sub = _jwt_claim(token, "sub")
        if sub:
            return f"user:{sub}"
        email = _jwt_claim(token, "email")
        if email:
            return f"user:{email}"

    # Fall back to client IP.
    # X-Forwarded-For is the standard header set by Cloud Run / load balancers.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"
    if request.client:
        return f"ip:{request.client.host}"
    return "ip:unknown"


# ── In-memory rate limiter ─────────────────────────────────────────────


class InMemoryRateLimiter:
    """
    Sliding-window-log rate limiter backed by an in-memory dict.

    Stores a list of request timestamps per client key.  On each
    :meth:`acquire` call, timestamps outside the sliding window are
    pruned and the remaining count is compared against ``limit``.

    Thread-safe via :class:`asyncio.Lock` — safe to share across
    concurrent asyncio tasks within the same process.
    """

    def __init__(self, config: RateLimitConfig):
        self._config = config
        self._requests: defaultdict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    @property
    def config(self) -> RateLimitConfig:
        return self._config

    async def acquire(
        self, client_id: str
    ) -> tuple[bool, int, int]:
        """Record a request for *client_id* and determine whether it is allowed.

        Returns a tuple of ``(allowed, remaining, retry_after_seconds)``:

        * ``allowed``       – True if the request is within the limit.
        * ``remaining``     – requests left in the current window (0 when
                              rate-limited).
        * ``retry_after``   – seconds until the oldest request expires
                              (0 when allowed, >= 1 when rate-limited).
        """
        async with self._lock:
            now = time.monotonic()
            window_start = now - self._config.window_seconds

            # Prune timestamps that have fallen outside the sliding window
            bucket = self._requests[client_id]
            self._requests[client_id] = [
                ts for ts in bucket if ts > window_start
            ]
            bucket = self._requests[client_id]

            if len(bucket) >= self._config.limit:
                # Client has exhausted their quota — tell them how long
                # to wait for the oldest request to expire.
                retry_after = int(
                    bucket[0] + self._config.window_seconds - now
                )
                return False, 0, max(retry_after, 1)

            # Request is allowed — record the timestamp
            bucket.append(now)
            remaining = self._config.limit - len(bucket)
            return True, remaining, 0

    def reset(self) -> None:
        """Clear all stored request timestamps.  Intended for tests."""
        self._requests.clear()

    def get_state(self) -> dict:
        """Return a debug-friendly summary of the current rate-limit state."""
        return {
            "limit": self._config.limit,
            "window_seconds": self._config.window_seconds,
            "exempt_paths": sorted(self._config.exempt_paths),
            "active_clients": len(self._requests),
        }


# ── Redis-backed Rate Limiter ──────────────────────────────────────────


class RedisRateLimiter:
    """
    Redis-backed sliding-window rate limiter for distributed deployments.

    Uses Redis sorted sets to track request timestamps per client.
    Provides global rate limiting across multiple application instances.
    """

    def __init__(self, config: RateLimitConfig, redis_client: "redis.Redis"):
        if not REDIS_AVAILABLE:
            raise RuntimeError(
                "redis-py is not installed. Install with: pip install redis"
            )
        self._config = config
        self._redis = redis_client
        self._key_prefix = "ratelimit:"

    @property
    def config(self) -> RateLimitConfig:
        return self._config

    def _make_key(self, client_id: str) -> str:
        """Create Redis key for a client."""
        return f"{self._key_prefix}{client_id}"

    async def acquire(
        self, client_id: str
    ) -> tuple[bool, int, int]:
        """Record a request for *client_id* and determine whether it is allowed.

        Returns a tuple of ``(allowed, remaining, retry_after_seconds)``.
        """
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
        """Clear stored rate-limit state. Intended for tests."""
        pass

    def get_state(self) -> dict:
        """Return a debug-friendly summary of the rate-limit state."""
        return {
            "limit": self._config.limit,
            "window_seconds": self._config.window_seconds,
            "exempt_paths": sorted(self._config.exempt_paths),
            "type": "redis",
        }

    async def close(self) -> None:
        """Close the Redis connection."""
        await self._redis.close()


# ── Redis Connection Helper ─────────────────────────────────────────────


def _create_redis_client() -> Optional["redis.Redis"]:
    """Create a Redis client from environment variables.

    Supports REDIS_URL or individual vars: REDIS_HOST, REDIS_PORT,
    REDIS_PASSWORD, REDIS_USERNAME, REDIS_SSL.
    """
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


# ── Module-level singleton ─────────────────────────────────────────────

_rate_limiter: Optional[InMemoryRateLimiter] = None
_redis_rate_limiter: Optional[RedisRateLimiter] = None


def get_rate_limiter() -> InMemoryRateLimiter | RedisRateLimiter:
    """Return the process-wide rate limiter, initialising from env if needed.

    Uses Redis-backed limiter if REDIS_URL or REDIS_HOST is configured,
    otherwise falls back to in-memory limiter.
    """
    global _rate_limiter, _redis_rate_limiter

    redis_client = _create_redis_client()
    if redis_client:
        if _redis_rate_limiter is None:
            _redis_rate_limiter = RedisRateLimiter(
                RateLimitConfig.from_env(), redis_client
            )
        return _redis_rate_limiter

    if _rate_limiter is None:
        _rate_limiter = InMemoryRateLimiter(RateLimitConfig.from_env())
    return _rate_limiter


def init_rate_limiter(
    config: Optional[RateLimitConfig] = None,
) -> InMemoryRateLimiter | RedisRateLimiter:
    """(Re-)initialise the singleton rate limiter.

    Passing a custom ``config`` is useful in tests to set a low limit
    for verifying rate-limit behaviour quickly.
    """
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
