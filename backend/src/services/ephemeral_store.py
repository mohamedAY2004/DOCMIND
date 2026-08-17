"""Redis-backed single-use values with an in-process development fallback."""
from __future__ import annotations

import asyncio
import time
from typing import Optional


class EphemeralStore:
    def __init__(self, redis_client=None) -> None:
        self._redis = redis_client
        self._memory: dict[str, tuple[str, float]] = {}
        self._queues: dict[str, asyncio.Queue[str]] = {}
        self._lock = asyncio.Lock()

    def _sweep_expired(self, now: float) -> None:
        expired = [key for key, (_value, expiry) in self._memory.items() if expiry <= now]
        for key in expired:
            self._memory.pop(key, None)

    async def put(self, key: str, value: str, ttl_seconds: int) -> None:
        if self._redis is not None:
            await self._redis.set(key, value, ex=ttl_seconds)
            return
        async with self._lock:
            now = time.monotonic()
            self._sweep_expired(now)
            self._memory[key] = (value, now + ttl_seconds)

    async def consume(self, key: str) -> Optional[str]:
        if self._redis is not None:
            value = await self._redis.getdel(key)
            return value.decode() if isinstance(value, bytes) else value
        async with self._lock:
            item = self._memory.pop(key, None)
            if item is None or item[1] <= time.monotonic():
                return None
            return item[0]

    async def increment(self, key: str, ttl_seconds: int) -> int:
        if self._redis is not None:
            value = await self._redis.eval(
                "local value = redis.call('INCR', KEYS[1]); "
                "if value == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]); end; "
                "return value",
                1,
                key,
                ttl_seconds,
            )
            return int(value)
        async with self._lock:
            now = time.monotonic()
            self._sweep_expired(now)
            current, expiry = self._memory.get(key, ("0", 0.0))
            if expiry <= now:
                current = "0"
                expiry = now + ttl_seconds
            value = int(current) + 1
            self._memory[key] = (str(value), expiry)
            return value

    async def decrement(self, key: str) -> int:
        if self._redis is not None:
            value = int(await self._redis.decr(key))
            if value <= 0:
                await self._redis.delete(key)
                return 0
            return value
        async with self._lock:
            current, expiry = self._memory.get(key, ("0", 0.0))
            value = max(0, int(current) - 1)
            if value == 0 or expiry <= time.monotonic():
                self._memory.pop(key, None)
                return 0
            self._memory[key] = (str(value), expiry)
            return value

    async def enqueue(self, key: str, value: str) -> None:
        if self._redis is not None:
            await self._redis.lpush(key, value)
            return
        self._queues.setdefault(key, asyncio.Queue()).put_nowait(value)

    async def dequeue(self, key: str, timeout_seconds: int = 5) -> Optional[str]:
        if self._redis is not None:
            item = await self._redis.brpop(key, timeout=timeout_seconds)
            if item is None:
                return None
            value = item[1]
            return value.decode() if isinstance(value, bytes) else value
        queue = self._queues.setdefault(key, asyncio.Queue())
        try:
            return await asyncio.wait_for(queue.get(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            return None

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()


_fallback = EphemeralStore()


def store_for(app) -> EphemeralStore:
    return getattr(app.state, "ephemeral_store", _fallback)


async def build_store(redis_url: str | None) -> EphemeralStore:
    if not redis_url:
        return _fallback
    from redis.asyncio import from_url
    client = from_url(redis_url, decode_responses=True)
    await client.ping()
    return EphemeralStore(client)
