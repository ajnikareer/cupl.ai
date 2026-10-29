"""In-process pub/sub so background jobs (plan builds, learning) can talk to live voice sessions."""
import asyncio
from collections import defaultdict

_subs: dict[str, set[asyncio.Queue]] = defaultdict(set)


def subscribe(uid: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=50)
    _subs[uid].add(q)
    return q


def unsubscribe(uid: str, q: asyncio.Queue):
    _subs[uid].discard(q)


def publish(uids: list[str], event: dict):
    for u in uids:
        for q in list(_subs.get(u, ())):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass
