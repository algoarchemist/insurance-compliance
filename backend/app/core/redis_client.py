"""Redis client for caching, OTP storage, and session management."""

import redis.asyncio as redis
from config import settings

redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


async def get_redis() -> redis.Redis:
    """Dependency to provide Redis client."""
    return redis_client


async def store_otp(key: str, value: str, ttl: int = 600) -> None:
    """Store OTP with TTL (default 10 minutes)."""
    await redis_client.setex(key, ttl, value)


async def get_otp(key: str) -> str | None:
    """Get stored OTP value."""
    return await redis_client.get(key)


async def delete_key(key: str) -> None:
    """Delete a Redis key."""
    await redis_client.delete(key)


async def blacklist_token(token: str, ttl: int = 604800) -> None:
    """Blacklist a JWT token (default 7 days TTL)."""
    await redis_client.setex(f"blacklist:{token}", ttl, "1")


async def is_token_blacklisted(token: str) -> bool:
    """Check if a token is blacklisted."""
    result = await redis_client.get(f"blacklist:{token}")
    return result is not None


async def cache_set(key: str, value: str, ttl: int = 3600) -> None:
    """Set a cached value with TTL."""
    await redis_client.setex(key, ttl, value)


async def cache_get(key: str) -> str | None:
    """Get a cached value."""
    return await redis_client.get(key)
