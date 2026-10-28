"""Couple Taste DNA from SHARED tastes only."""
import asyncio
import logging

from ..core.llm import gen_json
from ..db import db, get_doc, now_iso
from . import qloo
from .taste_intel import CATEGORIES
from .tastes import facts

log = logging.getLogger("dna")


def _key(f):
    return f.get("qloo_entity_id") or f.get("qloo_tag_id") or f.get("text", "").lower()


async def compute(couple_id: str) -> dict:
    couple = await get_doc(f"couples/{couple_id}")
    members = couple.get("members", [])
    users = await asyncio.gather(*[get_doc(f"users/{u}") for u in members])
    all_facts = await asyncio.gather(*[facts(u) for u in members])
    names, likes = {}, {}
    for uid, u, fs in zip(members, users, all_facts):
        names[uid] = (u or {}).get("name", "Partner")
        likes[uid] = {_key(f): f for f in fs if f.get("visibility", "shared") == "shared" and f.get("source") != "hint"
                      and f.get("sentiment", 0) > 0}
    cats = sorted({f["category"] for d in likes.values() for f in d.values()})
    shared, overlap, differences, shared_keys = [], {}, [], set()
    if len(members) == 2:
        a, b = members
        for cat in cats:
            la = {k: f for k, f in likes[a].items() if f["category"] == cat}
            lb = {k: f for k, f in likes[b].items() if f["category"] == cat}
            inter = set(la) & set(lb)
            if la and lb:
                overlap[cat] = round(100 * len(inter) / len(set(la) | set(lb)))
            for k in inter:
                shared.append({"category": cat, "name": la[k]["text"], "entity_id": la[k].get("qloo_entity_id"),
                               "image": la[k].get("image")})
                shared_keys.add(k)
            qtypes = CATEGORIES.get(cat, {}).get("types", [])
            if len(la) >= 2 and len(lb) >= 2 and not inter:
                diff = {"category": cat, "a_name": names[a], "a": [f["text"] for f in la.values()][:4],
                        "b_name": names[b], "b": [f["text"] for f in lb.values()][:4], "middle_ground": None}
                ids = [f["qloo_entity_id"] for f in list(la.values()) + list(lb.values()) if f.get("qloo_entity_id")]
                if qtypes and ids:
                    try:
                        res = await qloo.insights(qtypes[0], ids, take=5)
                        own = {f.get("qloo_entity_id") for f in list(la.values()) + list(lb.values())}
                        mg = next((r for r in res if r["entity_id"] not in own), None)
                        diff["middle_ground"] = mg["name"] if mg else None
                    except Exception as e:  # noqa
                        log.warning("middle ground failed: %s", e)
                differences.append(diff)
    unique = [{"name": names[u], "items": [{"category": f["category"], "name": f["text"], "image": f.get("image")}
                                           for k, f in likes[u].items() if k not in shared_keys][:30]} for u in members]
    all_names = [f"{f['category']}: {f['text']}" for d in likes.values() for f in d.values()][:60]
    vibe = {"vibe": "", "description": "", "palette": []}
    if all_names:
        try:
            vibe = await gen_json(
                "Write a couple 'vibe' from their tastes. vibe = 3-5 evocative words (e.g. 'Soulful, coastal, "
                "vintage-romantic'); description = one warm sentence addressed to them; palette = 4 hex colours.\n"
                f"Shared loves: {[s['name'] for s in shared]}\nAll tastes: {all_names}",
                {"type": "OBJECT", "properties": {"vibe": {"type": "STRING"}, "description": {"type": "STRING"},
                 "palette": {"type": "ARRAY", "items": {"type": "STRING"}}}, "required": ["vibe", "description", "palette"]},
                temperature=0.7)
        except Exception as e:  # noqa
            log.warning("vibe failed: %s", e)
    dna = {"shared": shared, "unique": unique, "overlap": overlap, "differences": differences,
           "vibe": vibe.get("vibe", ""), "description": vibe.get("description", ""),
           "palette": [p for p in vibe.get("palette", []) if isinstance(p, str) and p.startswith("#")][:4],
           "partners": [names[u] for u in members], "version": ((couple.get("dna") or {}).get("version", 0)) + 1,
           "updated_at": now_iso()}
    await db.document(f"couples/{couple_id}").update({"dna": dna})
    return dna
