"""Learning loop: conversation -> taste_intel (extract+resolve) -> facts; decisions; experiences;
profile details; rolling summary -> DNA -> re-plan only affected sections. Also retries unresolved tastes."""
import asyncio
import logging

from ..core.llm import gen_json
from ..db import db, get_doc, new_id, now_iso
from . import dna as dna_svc
from . import plan_engine, taste_intel
from .couple import partner_uid
from .memory import save_episode, turns_since
from .notify import notify
from .tastes import facts, save_fact, save_resolution

log = logging.getLogger("learning")
_running: set[str] = set()
_tasks: set[asyncio.Task] = set()

META_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "decisions": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
            "summary": {"type": "STRING"}, "is_surprise": {"type": "BOOLEAN"}}, "required": ["summary", "is_surprise"]}},
        "experience": {"type": "OBJECT", "properties": {
            "has_experience": {"type": "BOOLEAN"}, "summary": {"type": "STRING"}, "rating": {"type": "NUMBER"},
            "highlights": {"type": "ARRAY", "items": {"type": "STRING"}},
            "lowlights": {"type": "ARRAY", "items": {"type": "STRING"}}, "is_surprise": {"type": "BOOLEAN"}}},
        "profile": {"type": "OBJECT", "properties": {
            "partner_name": {"type": "STRING"}, "how_met": {"type": "STRING"}, "relationship_since": {"type": "STRING"},
            "hometown": {"type": "STRING"}, "family_notes": {"type": "STRING"}, "culture": {"type": "STRING"}}},
        "summary": {"type": "STRING", "description": "rolling summary of the whole relationship with the user so far, <=120 words"},
        "mentions_surprise": {"type": "BOOLEAN"},
    },
    "required": ["decisions", "summary", "mentions_surprise"],
}


async def run(uid: str):
    if uid in _running:
        return
    _running.add(uid)
    try:
        await _run(uid)
        await retry_unresolved(uid)
    except Exception:  # noqa
        log.exception("learning failed for %s", uid)
    finally:
        _running.discard(uid)


def _user_lines(turns: list[dict]) -> str:
    # skip deterministic picker/form echoes — they are already saved precisely
    return "\n".join(t["text"] for t in turns if t["role"] == "user" and t.get("text") and not t["text"].startswith("["))


async def _run(uid: str):
    conv = await get_doc(f"conversations/{uid}") or {}
    turns = [t for t in await turns_since(uid, conv.get("learned_upto")) if t.get("text")]
    if not turns:
        return
    user = await get_doc(f"users/{uid}")
    couple = await get_doc(f"couples/{user['couple_id']}") or {"members": [uid]}
    p_uid = partner_uid(couple, uid)
    partner = await get_doc(f"users/{p_uid}") if p_uid else None
    pname = (partner or {}).get("name") or (user.get("profile") or {}).get("partner_name") or "their partner"
    transcript = "\n".join(f"{'USER' if t['role'] == 'user' else 'PLANNER'}: {t['text']}" for t in turns)[-12000:]
    said = _user_lines(turns)

    meta_task = gen_json(
        f"From this conversation between {user.get('name')} and their wedding/couple planner, extract:\n"
        "- decisions the couple agreed on (concrete planning choices). is_surprise=true if it relates to a secret surprise.\n"
        "- experience: only if the user describes how a past event/trip went.\n"
        "- profile: personal details the user stated (partner's name, how they met, since when together, hometown, "
        "family notes, culture/traditions). Leave empty if not stated.\n"
        f"- summary: update this rolling summary with anything new: \"{conv.get('summary', '')}\"\n"
        "- mentions_surprise: true if the user is planning a secret surprise for their partner.\n\n"
        f"CONVERSATION:\n{transcript}", META_SCHEMA, temperature=0.1)
    extract_task = taste_intel.extract(said, user.get("name") or "the user", pname) if said.strip() else _empty()
    meta, items = await asyncio.gather(meta_task, extract_task)

    changed_cats = set()
    mine = await facts(uid)
    theirs = await facts(p_uid) if p_uid else []
    for it in items:
        if it["confidence"] < 0.55:
            continue
        target = uid if it["about"] == "self" else p_uid
        if not target:
            continue
        res = await taste_intel.resolve(it["mention"], it["category"], it["kind"], it.get("context_hint") or "")
        if target == uid:
            await save_resolution(uid, res, it["sentiment"], it["confidence"], "chat", existing=mine)
            changed_cats.add(res["category"])
        else:   # a hint about the partner: private, low confidence, partner can confirm it
            if not meta.get("mentions_surprise"):
                await save_resolution(p_uid, res, it["sentiment"], 0.4, "hint", visibility="private", existing=theirs)
    for d in meta.get("decisions", [])[:5]:
        doc = {"summary": d["summary"][:300], "by_uid": uid, "space_id": user.get("active_space_id"), "at": now_iso()}
        if d.get("is_surprise") or meta.get("mentions_surprise"):
            doc["private_to"] = uid
        await db.document(f"couples/{user['couple_id']}/decisions/{new_id('d')}").set(doc)
    exp = meta.get("experience") or {}
    if exp.get("has_experience") and exp.get("summary") and not exp.get("is_surprise"):
        await save_episode(user["couple_id"], exp["summary"], user.get("active_space_id"), exp.get("rating"),
                           exp.get("highlights"), exp.get("lowlights"), uid)
    prof = {k: v[:200] for k, v in (meta.get("profile") or {}).items() if isinstance(v, str) and v.strip()}
    if prof:
        await db.document(f"users/{uid}").set({"profile": prof}, merge=True)
    await db.document(f"conversations/{uid}").set(
        {"learned_upto": turns[-1]["ts"], "summary": (meta.get("summary") or conv.get("summary", ""))[:1500]}, merge=True)

    if changed_cats:
        await dna_svc.compute(user["couple_id"])
        sid = user.get("active_space_id")
        space = await get_doc(f"spaces/{sid}") if sid else None
        if space and space.get("state") == "planned":
            keys = plan_engine.sections_for_categories(space["type"], changed_cats)
            if keys:
                await plan_engine.start_build(sid, keys, "Refreshed with newly learned tastes", uid)
        else:
            await notify(uid, "I learned something new about your tastes 💡", "/app/me", "learning")


async def retry_unresolved(uid: str):
    for f in [f for f in await facts(uid) if f.get("resolution") == "unresolved" and f.get("resolve_attempts", 0) < 3][:10]:
        res = await taste_intel.resolve(f["text"], f["category"], "entity")
        upd = {"resolve_attempts": f.get("resolve_attempts", 0) + 1}
        if res["status"] == "resolved":
            upd.update({"qloo_entity_id": res.get("entity_id"), "qloo_type": res.get("qloo_type"),
                        "qloo_tag_id": res.get("tag_id"), "image": res.get("image"), "resolution": "resolved"})
        await db.document(f"users/{uid}/facts/{f['id']}").update(upd)


async def _empty():
    return []


def schedule(uid: str):
    t = asyncio.create_task(run(uid))
    _tasks.add(t)
    t.add_done_callback(_tasks.discard)
