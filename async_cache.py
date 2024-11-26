import asyncio
import json
from django.core.cache import cache


class AsyncCache:
    async def aget(self, key):
        loop = asyncio.get_event_loop()
        value = await loop.run_in_executor(None, cache.get, key)
        return json.loads(value) if value else None

    async def aset(self, key, value):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, cache.set, key, json.dumps(value))


# Использование асинхронного кэша
async_cache = AsyncCache()
