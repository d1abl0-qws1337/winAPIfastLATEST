import json
from typing import Optional, Any
import redis.asyncio as redis
from app.config import settings


class RedisCache:
    """Redis cache manager for application data."""

    def __init__(self):
        self.client: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis server."""
        if not self.client:
            self.client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )

    async def disconnect(self):
        """Disconnect from Redis server."""
        if self.client:
            await self.client.close()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        await self.connect()
        value = await self.client.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: int = 300
    ) -> bool:
        """Set value in cache with expiration."""
        await self.connect()
        return await self.client.set(
            key,
            json.dumps(value),
            ex=expire
        )

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        await self.connect()
        return await self.client.delete(key) > 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        await self.connect()
        return await self.client.exists(key) > 0

    async def get_json(self, key: str) -> Optional[dict]:
        """Get JSON object from cache."""
        value = await self.get(key)
        if value:
            return value
        return None

    async def set_json(
        self,
        key: str,
        value: dict,
        expire: int = 300
    ) -> bool:
        """Set JSON object in cache."""
        return await self.set(key, value, expire)

    async def invalidate_user_cache(self, user_id: int):
        """Invalidate all cache entries for a user."""
        pattern = f"user:{user_id}:*"
        await self.connect()
        keys = await self.client.keys(pattern)
        if keys:
            await self.client.delete(*keys)


cache = RedisCache()
