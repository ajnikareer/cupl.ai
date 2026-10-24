"""Taste facts store. A fact is one taste of one person, ideally grounded to a QLOO entity or tag."""
import asyncio

from ..db import db, list_col, new_id, now_iso
from . import qloo
from .taste_intel import CATEGORIES

MAX_FACTS = 400


async def facts(uid: str | None) -> list[dict]:
    if not uid:
        return []
    items = await list_col(db.collection(f"users/{uid}/facts"), limit=MAX_FACTS)
    return [f for f in items if not f.get("superseded_by")]


def visible_facts(viewer_uid: str, owner_uid: str, items: list[dict]) -> list[dict]:
    if viewer_uid == owner_uid:
        return items
    return [f for f in items if f.get("visibility", "shared") == "shared" and f.get("source") != "hint"]


def _same(f: dict, entity_id, tag_id, text, category) -> bool:
    if entity_id and f.get("qloo_entity_id") == entity_id:
        return True
    if tag_id and f.get("qloo_tag_id") == tag_id:
        return True
    return f.get("category") == category and f.get("text", "").lower() == (text or "").lower()


async def save_fact(uid: str, category: str, text: str, *, entity_id=None, qloo_type=None, tag_id=None,
                    image=None, sentiment=0.8, confidence=0.9, visibility="shared", source="picker",
                    resolution="resolved", candidates=None, existing: list[dict] | None = None) -> dict:
    category = category if category in CATEGORIES else "experience"
    text = (text or "").strip()[:120]
    if not text:
        return {}
    col = db.collection(f"users/{uid}/facts")
    existing = existing if existing is not None else await facts(uid)
    match = next((f for f in existing if _same(f, entity_id, tag_id, text, category)), None)
    if match:
        upd = {"mentions": match.get("mentions", 1) + 1, "updated_at": now_iso()}
        if (match.get("sentiment", 0) > 0) != (sentiment > 0):          # opinion changed: newest wins
            upd.update({"sentiment": sentiment, "confidence": confidence})
        else:
            upd["confidence"] = round(min(1.0, max(match.get("confidence", 0.5), confidence) + 0.05), 3)
        if source not in ("hint",) and match.get("source") == "hint":   # partner confirmed own taste
            upd.update({"source": source, "visibility": visibility})
        if entity_id and not match.get("qloo_entity_id"):
            upd.update({"qloo_entity_id": entity_id, "qloo_type": qloo_type, "resolution": "resolved"})
        if tag_id and not match.get("qloo_tag_id"):
            upd.update({"qloo_tag_id": tag_id, "resolution": "resolved"})
        await col.document(match["id"]).update(upd)
        match.update(upd)
        return match
    fid = new_id("f")
    doc = {"category": category, "text": text, "qloo_entity_id": entity_id, "qloo_type": qloo_type,
           "qloo_tag_id": tag_id, "image": image, "sentiment": round(float(sentiment), 2),
           "confidence": round(float(confidence), 2), "visibility": visibility, "source": source,
           "resolution": resolution if not (entity_id or tag_id) else "resolved", "resolve_attempts": 0,
           "candidates": candidates or None, "mentions": 1, "created_at": now_iso(), "updated_at": now_iso(),
           "superseded_by": None}
    await col.document(fid).set(doc)
    doc["id"] = fid
    existing.append(doc)
    return doc


async def save_resolution(uid: str, res: dict, sentiment: float, confidence: float, source: str,
                          visibility: str = "shared", existing: list[dict] | None = None) -> dict:
    """Persist a taste_intel resolution result."""
    if res["status"] == "resolved":
        return await save_fact(uid, res["category"], res.get("name") or res["mention"], entity_id=res.get("entity_id"),
                               qloo_type=res.get("qloo_type"), tag_id=res.get("tag_id"), image=res.get("image"),
                               sentiment=sentiment, confidence=confidence, visibility=visibility, source=source,
                               existing=existing)
    return await save_fact(uid, res["category"], res["mention"], sentiment=sentiment, confidence=confidence,
                           visibility=visibility, source=source, resolution=res["status"],
                           candidates=res.get("candidates"), existing=existing)


def signals(items: list[dict], limit: int = 15) -> dict:
    """Only grounded, positive tastes become QLOO signals."""
    liked = sorted([f for f in items if f.get("sentiment", 0) > 0 and (f.get("qloo_entity_id") or f.get("qloo_tag_id"))],
                   key=lambda f: (f.get("confidence", 0) * (1 + 0.1 * min(f.get("mentions", 1), 5)), f.get("updated_at", "")),
                   reverse=True)
    return {"entities": [f["qloo_entity_id"] for f in liked if f.get("qloo_entity_id")][:limit],
            "tags": [f["qloo_tag_id"] for f in liked if f.get("qloo_tag_id")][:6]}


def disliked_ids(items: list[dict]) -> set:
    return {f["qloo_entity_id"] for f in items if f.get("qloo_entity_id") and f.get("sentiment", 0) < 0}


def coverage(items: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for f in items:
        if f.get("sentiment", 0) > 0 and f.get("source") != "hint":
            out[f["category"]] = out.get(f["category"], 0) + 1
    return out


async def suggest(category: str, uid: str, partner_uid: str | None, city: str | None = None,
                  mine: list[dict] | None = None, theirs: list[dict] | None = None) -> list[dict]:
    """Live suggestions for a picker: partner's shared picks first (💞), then QLOO recommendations."""
    from ..core.llm import gen_json
    if mine is None or theirs is None:
        mine, raw = await asyncio.gather(facts(uid), facts(partner_uid))
        theirs = visible_facts(uid, partner_uid, raw) if partner_uid else []
    have = {(f.get("qloo_entity_id") or f.get("text", "").lower()) for f in mine if f.get("category") == category}
    out, seen = [], set()
    for f in theirs:
        if f.get("category") == category and f.get("sentiment", 0) > 0:
            key = f.get("qloo_entity_id") or f["text"].lower()
            if key in seen or key in have:
                continue
            seen.add(key)
            out.append({"name": f["text"], "entity_id": f.get("qloo_entity_id"), "image": f.get("image"),
                        "partner_likes": True})
    qtypes = CATEGORIES.get(category, {}).get("types", [])
    if qtypes:
        s_me, s_them = signals(mine, 8), signals(theirs, 7)
        res = await qloo.insights(qtypes[0], s_me["entities"] + s_them["entities"], s_me["tags"] + s_them["tags"],
                                  city if qtypes[0] == qloo.PLACE else None, take=18)
        for e in res:
            if e["entity_id"] in seen or e["entity_id"] in have:
                continue
            seen.add(e["entity_id"])
            out.append({"name": e["name"], "entity_id": e["entity_id"], "image": e.get("image"), "partner_likes": False})
    else:
        known = [f["text"] for f in mine + theirs if f.get("sentiment", 0) > 0][:25]
        data = await gen_json(
            f"Suggest 10 short, specific options for '{CATEGORIES[category]['label']}' an Indian couple"
            f"{' in ' + city if city else ''} might love. Already known likes: {known}. Mix classic and distinctive. "
            "Names only, 1-4 words each.",
            {"type": "OBJECT", "properties": {"options": {"type": "ARRAY", "items": {"type": "STRING"}}},
             "required": ["options"]}, temperature=0.8)
        for n in data.get("options", [])[:10]:
            if n.lower() not in have and n.lower() not in seen:
                seen.add(n.lower())
                out.append({"name": n, "entity_id": None, "image": None, "partner_likes": False})
    return out[:16]
