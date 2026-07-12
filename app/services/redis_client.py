import redis.asyncio as redis

from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def is_duplicate_update(update_id: int) -> bool:
    """Atomically mark an update as seen. Returns True if already processed."""
    key = f"tg:update:{update_id}"
    was_set = await redis_client.set(key, "1", nx=True, ex=300)
    return was_set is None
