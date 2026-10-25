"""Deterministic handling of taps on chat widgets (no LLM guessing at the input point).
Picks from the taste picker already carry QLOO entity IDs; custom typed names are resolved with the KNOWN category."""
import asyncio

from ..db import db
from ..services import spaces as sp
from ..services import state, taste_intel, tastes
from ..services.memory import mark_widget_done


async def apply(uid: str, wr: dict) -> str:
    """Persist the user's widget answer and return a short text the agent sees as the user's turn."""
    w = await mark_widget_done(uid, wr.get("widget_id"), wr.get("values")) or {}
    kind = wr.get("kind") or w.get("kind")
    title = w.get("title") or wr.get("title") or ""
    values = wr.get("values")

    if kind == "taste_picker":
        category = w.get("category") or wr.get("category") or "experience"
        sentiment = -0.8 if (w.get("sentiment") or wr.get("sentiment")) == "dislike" else 0.85
        existing = await tastes.facts(uid)
        picks = [v for v in (values or []) if isinstance(v, dict) and (v.get("name") or "").strip()][:10]
        unresolved = [v for v in picks if not v.get("entity_id")]
        resolutions = await asyncio.gather(*[taste_intel.resolve(v["name"].strip(), category, "entity") for v in unresolved])
        rmap = {id(v): r for v, r in zip(unresolved, resolutions)}
        names, unclear = [], []
        for v in picks:
            if v.get("entity_id"):
                qtype = (taste_intel.CATEGORIES.get(category, {}).get("types") or [None])[0]
                f = await tastes.save_fact(uid, category, v["name"].strip(), entity_id=v["entity_id"], qloo_type=qtype,
                                           image=v.get("image"), sentiment=sentiment, confidence=0.95, source="picker",
                                           existing=existing)
                names.append(f.get("text"))
            else:
                r = rmap[id(v)]
                if r["status"] == "ambiguous":
                    unclear.append(v["name"])
                await tastes.save_resolution(uid, r, sentiment, 0.9, "picker", existing=existing)
                names.append(r.get("name") or v["name"])
        verb = "I don't like" if sentiment < 0 else "My picks"
        extra = f" (couldn't pin down exactly: {', '.join(unclear)})" if unclear else ""
        return f"[picked · {title}] {verb}: {', '.join(names) or 'none'}{extra}"

    if kind == "disambiguation":
        choice = values if isinstance(values, dict) else None
        if not choice or not choice.get("entity_id"):
            return f"[clarified] None of those options — it's something else: “{w.get('mention')}”."
        target = uid
        if w.get("about") == "partner":
            snap = await state.load(uid, with_episodes=False)
            target = (snap.partner or {}).get("id")
        if target:
            await tastes.save_fact(target, w.get("category", "experience"), choice["name"], entity_id=choice["entity_id"],
                                   qloo_type=choice.get("qloo_type"), image=choice.get("image"),
                                   sentiment=float(w.get("sentiment", 0.8)),
                                   confidence=0.95 if target == uid else 0.4, source="picker" if target == uid else "hint",
                                   visibility="shared" if target == uid else "private")
        return f"[clarified] I meant {choice.get('label') or choice['name']}."

    if kind == "space_form":
        user = (await state.load(uid, with_episodes=False)).user
        sid = w.get("space_id") or wr.get("space_id") or user.get("active_space_id")
        errors = []
        if sid:
            _, errors = await sp.update_space(sid, user["couple_id"], values or {})
        return f"[saved event details] {values}" + (f" — but: {'; '.join(errors)}" if errors else "")

    if kind == "choices":
        v = values if isinstance(values, list) else [values]
        await state.bump_taste_streak(uid, reset=True)
        return f"[chose · {title}] {', '.join(str(x) for x in v)}"

    if kind == "confirm":
        return f"[{'YES — go ahead' if values else 'NO — cancel that'}] {title}"

    return f"[{kind}] {values}"
