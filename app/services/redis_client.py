import json

import redis.asyncio as redis

from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def is_duplicate_update(update_id: int) -> bool:
    """Atomically mark an update as seen. Returns True if already processed."""
    key = f"tg:update:{update_id}"
    was_set = await redis_client.set(key, "1", nx=True, ex=300)
    return was_set is None


async def cache_get(key: str) -> dict | list | None:
    raw = await redis_client.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def cache_set(key: str, value: dict | list, *, ex: int = 30) -> None:
    await redis_client.set(key, json.dumps(value), ex=ex)


async def cache_invalidate_chat(chat_id: int) -> None:
    """
    Drops every cached Mini App response for a chat. Called whenever a PO
    is created or its status changes, since dashboard/history reads are
    cached but must never serve stale data after a write.
    """
    pattern = f"webapp:{chat_id}:*"
    keys = [key async for key in redis_client.scan_iter(match=pattern, count=100)]
    if keys:
        await redis_client.delete(*keys)