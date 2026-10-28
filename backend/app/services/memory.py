"""Episodic memory (vector recall) + conversation store."""
import logging

from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from google.cloud.firestore_v1.vector import Vector

from ..core.llm import embed
from ..db import db, doc_dict, new_id, now_iso

log = logging.getLogger("memory")
_vector_ok = True


async def save_episode(couple_id: str, summary: str, space_id: str | None = None, rating: float | None = None,
                       highlights: list | None = None, lowlights: list | None = None, by_uid: str | None = None) -> dict:
    doc = {"couple_id": couple_id, "space_id": space_id, "summary": summary[:1500], "rating": rating,
           "highlights": (highlights or [])[:8], "lowlights": (lowlights or [])[:8], "by_uid": by_uid, "created_at": now_iso()}
    try:
        doc["embedding"] = Vector(await embed(" ".join([summary, *doc["highlights"], *doc["lowlights"]])))
    except Exception as e:  # noqa
        log.warning("embedding failed: %s", e)
    eid = new_id("e")
    await db.document(f"episodes/{eid}").set(doc)
    doc.pop("embedding", None)
    doc["id"] = eid
    return doc


async def list_episodes(couple_id: str) -> list[dict]:
    out = [doc_dict(s) async for s in
           db.collection("episodes").where(filter=FieldFilter("couple_id", "==", couple_id)).limit(200).stream()]
    out = [o for o in out if o]
    out.sort(key=lambda e: e.get("created_at", ""), reverse=True)
    return out


async def recall(couple_id: str, query: str, k: int = 3) -> list[dict]:
    global _vector_ok
    eps = await list_episodes(couple_id)
    if len(eps) <= k:               # nothing to rank — skip the embedding call (latency)
        return eps
    if _vector_ok:
        try:
            vec = await embed(query)
            q = (db.collection("episodes").where(filter=FieldFilter("couple_id", "==", couple_id))
                 .find_nearest(vector_field="embedding", query_vector=Vector(vec),
                               distance_measure=DistanceMeasure.COSINE, limit=k))
            res = [doc_dict(s) async for s in q.stream()]
            return [r for r in res if r]
        except Exception as e:  # noqa
            if "index" in str(e).lower():
                _vector_ok = False
            log.warning("vector recall fallback: %s", e)
    return eps[:k]


# ---------------- conversation store ----------------
async def add_turn(uid: str, role: str, text: str, widget: dict | None = None, channel: str = "text") -> int:
    ts = now_iso()
    await db.document(f"conversations/{uid}/turns/{new_id('m')}").set(
        {"role": role, "text": text or "", "widget": widget, "channel": channel, "ts": ts})
    ref = db.document(f"conversations/{uid}")
    snap = await ref.get()
    count = ((snap.to_dict() or {}).get("turn_count", 0) if snap.exists else 0) + 1
    await ref.set({"turn_count": count, "updated_at": ts}, merge=True)
    return count


async def recent_turns(uid: str, n: int = 20) -> list[dict]:
    q = db.collection(f"conversations/{uid}/turns").order_by("ts", direction="DESCENDING").limit(n)
    out = [doc_dict(s) async for s in q.stream()]
    return list(reversed([o for o in out if o]))


async def turns_since(uid: str, since: str | None, n: int = 80) -> list[dict]:
    col = db.collection(f"conversations/{uid}/turns")
    q = col.where(filter=FieldFilter("ts", ">", since)) if since else col
    out = [doc_dict(s) async for s in q.order_by("ts").limit(n).stream()]
    return [o for o in out if o]


async def mark_widget_done(uid: str, widget_id: str, values):
    q = db.collection(f"conversations/{uid}/turns").order_by("ts", direction="DESCENDING").limit(40)
    async for s in q.stream():
        w = (s.to_dict() or {}).get("widget")
        if w and w.get("id") == widget_id:
            w["done"] = True
            w["values"] = values
            await s.reference.update({"widget": w})
            return w
    return None
