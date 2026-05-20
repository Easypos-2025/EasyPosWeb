import asyncio

_sse_subscribers: set[asyncio.Queue] = set()


async def sse_generator(queue: asyncio.Queue):
    try:
        yield "event: connected\ndata: ok\n\n"
        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=25)
                yield msg
            except asyncio.TimeoutError:
                yield ": heartbeat\n\n"
    finally:
        _sse_subscribers.discard(queue)


def notify_landing_changed():
    msg = "event: landing_updated\ndata: ok\n\n"
    for q in list(_sse_subscribers):
        try:
            q.put_nowait(msg)
        except (asyncio.QueueFull, Exception):
            _sse_subscribers.discard(q)
