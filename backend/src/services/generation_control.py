"""Shared concurrency and cancellation controls for generated replies."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, AsyncIterator, Awaitable, TypeVar

from fastapi import status

from helpers.config import get_settings
from helpers.errors import APIError, ErrorCode
from services.ephemeral_store import EphemeralStore

T = TypeVar("T")


class GenerationCancelled(Exception):
    """Raised internally when a reply cancellation marker is observed."""


@dataclass
class GenerationSlot:
    store: EphemeralStore
    key: str
    released: bool = False

    @classmethod
    async def acquire(cls, store: EphemeralStore, user_id: str) -> "GenerationSlot":
        settings = get_settings()
        key = f"generation:active:{user_id}"
        count = await store.increment(key, settings.GENERATION_SLOT_TTL_SECONDS)
        if count > settings.MAX_CONCURRENT_GENERATIONS:
            await store.decrement(key)
            raise APIError(
                ErrorCode.RATE_LIMITED,
                status.HTTP_429_TOO_MANY_REQUESTS,
                f"Only {settings.MAX_CONCURRENT_GENERATIONS} generations may run at the same time.",
            )
        return cls(store=store, key=key)

    async def release(self) -> None:
        if not self.released:
            self.released = True
            await self.store.decrement(self.key)


def cancellation_key(reply_id: str) -> str:
    return f"generation:cancel:{reply_id}"


async def request_cancellation(store: EphemeralStore, reply_id: str) -> None:
    await store.put(cancellation_key(reply_id), "1", get_settings().GENERATION_SLOT_TTL_SECONDS)


async def _cancel_requested(store: EphemeralStore, reply_id: str) -> bool:
    return await store.consume(cancellation_key(reply_id)) is not None


async def iter_cancellable(
    source: AsyncIterator[T],
    *,
    store: EphemeralStore,
    reply_id: str,
    poll_seconds: float = 0.25,
) -> AsyncIterator[T]:
    """Iterate a provider stream while polling a cheap cancellation marker."""
    iterator = source.__aiter__()
    while True:
        next_item = asyncio.create_task(anext(iterator))
        try:
            while not next_item.done():
                await asyncio.wait({next_item}, timeout=poll_seconds)
                if not next_item.done() and await _cancel_requested(store, reply_id):
                    next_item.cancel()
                    await asyncio.gather(next_item, return_exceptions=True)
                    close = getattr(iterator, "aclose", None)
                    if close is not None:
                        await close()
                    raise GenerationCancelled
            try:
                yield next_item.result()
            except StopAsyncIteration:
                return
        finally:
            if not next_item.done():
                next_item.cancel()
                await asyncio.gather(next_item, return_exceptions=True)


async def await_cancellable(
    awaitable: Awaitable[T],
    *,
    store: EphemeralStore,
    reply_id: str,
    poll_seconds: float = 0.25,
) -> T:
    """Await a buffered agent call without losing cancellation responsiveness."""
    task = asyncio.create_task(awaitable)
    try:
        while not task.done():
            await asyncio.wait({task}, timeout=poll_seconds)
            if not task.done() and await _cancel_requested(store, reply_id):
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
                raise GenerationCancelled
        return task.result()
    finally:
        if not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
