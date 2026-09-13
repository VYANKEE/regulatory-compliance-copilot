"""
Redis client -- used for per-user rate limiting and retrieval/analysis
response caching.

Lazy connection: get_redis() builds the pool immediately, but TCP connect
only happens on the first real command, so the app still boots if Redis is
down. check_rate_limit fails open in that case -- availability over
strictness for this non-critical layer.
"""

import time

import redis

from .config import get_settings

_client: "redis.Redis | None" = None


def get_redis() -> "redis.Redis":
    global _client
    if _client is None:
        settings = get_settings()
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def check_rate_limit(key: str, limit_per_minute: int | None = None) -> bool:
    """Fixed-window (per-minute bucket) rate limit. Returns True if allowed,
    False if over limit. Fails open (True) if Redis is unreachable."""
    settings = get_settings()
    limit = limit_per_minute or settings.rate_limit_requests_per_minute
    bucket = int(time.time() // 60)
    redis_key = f"ratelimit:{key}:{bucket}"
    try:
        client = get_redis()
        count = client.incr(redis_key)
        if count == 1:
            client.expire(redis_key, 60)
        return count <= limit
    except redis.RedisError:
        return True
