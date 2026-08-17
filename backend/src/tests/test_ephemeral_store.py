from services.ephemeral_store import EphemeralStore
import time
import asyncio
import pytest

from services.generation_control import (
    GenerationCancelled,
    iter_cancellable,
    request_cancellation,
)


async def test_memory_counter_releases_generation_slot():
    store = EphemeralStore()
    assert await store.increment("generation:user", 60) == 1
    assert await store.increment("generation:user", 60) == 2
    assert await store.decrement("generation:user") == 1
    assert await store.decrement("generation:user") == 0


async def test_memory_queue_wakes_worker_once():
    store = EphemeralStore()
    await store.enqueue("evaluation:runs", "run_1")
    assert await store.dequeue("evaluation:runs", timeout_seconds=1) == "run_1"


async def test_memory_store_sweeps_expired_keys_on_write():
    store = EphemeralStore()
    store._memory["expired"] = ("1", time.monotonic() - 1)
    await store.put("fresh", "1", 60)
    assert "expired" not in store._memory
    assert "fresh" in store._memory


async def test_cancellation_interrupts_provider_that_has_not_emitted_a_delta():
    store = EphemeralStore()

    async def stalled():
        await asyncio.sleep(10)
        yield "too late"

    controlled = iter_cancellable(
        stalled(), store=store, reply_id="reply-1", poll_seconds=0.01
    )
    pending = asyncio.create_task(anext(controlled))
    await asyncio.sleep(0.02)
    await request_cancellation(store, "reply-1")
    with pytest.raises(GenerationCancelled):
        await pending
