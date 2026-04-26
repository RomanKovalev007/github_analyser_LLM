import json
import os
import hashlib
import functools
import redis.asyncio as redis

CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

_redis: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis


def _make_key(prefix: str, kwargs: dict) -> str:
    payload = json.dumps(kwargs, sort_keys=True)
    h = hashlib.md5(payload.encode()).hexdigest()[:12]
    return f"gh:{prefix}:{h}"


def cached(prefix: str):
    def decorator(fn):
        @functools.wraps(fn)
        async def wrapper(**kwargs):
            r = await get_redis()
            key = _make_key(prefix, kwargs)
            cached_value = await r.get(key)
            if cached_value is not None:
                return cached_value
            result = await fn(**kwargs)
            await r.set(key, result, ex=CACHE_TTL)
            return result
        return wrapper
    return decorator
