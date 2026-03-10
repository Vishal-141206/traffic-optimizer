"""Redis connection and pub/sub management."""

import json
from typing import Optional, Any, Callable
import redis.asyncio as redis
from core.config import settings


class RedisManager:
    """Manages Redis connections and pub/sub operations."""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        
    async def connect(self):
        """Establish Redis connection."""
        self.redis = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        self.pubsub = self.redis.pubsub()
        
    async def disconnect(self):
        """Close Redis connection."""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()
            
    async def publish(self, channel: str, message: Any):
        """Publish message to a channel."""
        if self.redis:
            await self.redis.publish(channel, json.dumps(message))
            
    async def subscribe(self, channel: str, callback: Callable):
        """Subscribe to a channel with a callback."""
        if self.pubsub:
            await self.pubsub.subscribe(**{channel: callback})
            
    async def set(self, key: str, value: Any, expire: int = None):
        """Set a key-value pair with optional expiration."""
        if self.redis:
            await self.redis.set(key, json.dumps(value), ex=expire)
            
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key."""
        if self.redis:
            value = await self.redis.get(key)
            return json.loads(value) if value else None
        return None
    
    async def lpush(self, key: str, value: Any):
        """Push to left of a list."""
        if self.redis:
            await self.redis.lpush(key, json.dumps(value))
            
    async def rpop(self, key: str) -> Optional[Any]:
        """Pop from right of a list."""
        if self.redis:
            value = await self.redis.rpop(key)
            return json.loads(value) if value else None
        return None
    
    async def lrange(self, key: str, start: int, end: int) -> list:
        """Get range from list."""
        if self.redis:
            values = await self.redis.lrange(key, start, end)
            return [json.loads(v) for v in values]
        return []


# Global Redis manager instance
redis_manager = RedisManager()


async def get_redis() -> RedisManager:
    """Dependency for getting Redis manager."""
    if not redis_manager.redis:
        await redis_manager.connect()
    return redis_manager
