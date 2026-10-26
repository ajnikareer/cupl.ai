"""One parallel snapshot of everything the agent needs + the conversation Director.

The Director is what makes the agent feel like a human planner: it decides the ONE next move
(get to know them -> event basics one at a time -> tastes a little at a time -> partner -> plan -> refine
-> companion) and tells the agent what NOT to do (no interrogations, no form dumps, no repeats)."""
import asyncio
from dataclasses import dataclass, field

from ..core.timeutil import today
from ..db import get_doc, list_col, db
from . import spaces as sp
from .couple import decisions, partner_uid
from .memory import recall
from .tastes import coverage, facts, visible_facts
from .taste_intel import CATEGORIES


@dataclass
class Snapshot:
    user: dict
    couple: dict
    partner: dict | None
    mode: str
    space: dict | None
    spaces: list
    my_facts: list
    partner_facts: list            # visible to the user (shared only)
    decisions: list
    conv: dict
    episodes: list = field(default_factory=list)
    next: dict = field(default_factory=dict)


def mode_for(space: dict | None) -> str:
    if not space:
        return "guide"
    return "setup" if sp.missing_fields(space) else "planner"


async def load(uid: str, query: str = "", with_episodes: bool = True) -> Snapshot:
    user = await get_doc(f"users/{uid}")
    if not user:
        raise ValueError("unknown user")
    sid = user.get("active_space_id")
    couple, space, my, conv = await asyncio.gather(
        get_doc(f"couples/{user['couple_id']}"), get_doc(f"spaces/{sid}") if sid else _none(),
        facts(uid), get_doc(f"conversations/{uid}"))
    couple = couple or {"members": [uid]}
    if space and space.get("couple_id") != user["couple_id"]:
        space = None
    if space:
        space["missing_fields"] = sp.missing_fields(space)
    p_uid = partner_uid(couple, uid)
    partner, p_facts, spaces, decs = await asyncio.gather(
        get_doc(f"users/{p_uid}") if p_uid else _none(), facts(p_uid), sp.list_spaces(user["couple_id"]),
        decisions(user["couple_id"], 10))
    decs = [d for d in decs if not d.get("private_to") or d.get("private_to") == uid]
    snap = Snapshot(user=user, couple=couple, partner=partner, mode=mode_for(space), space=space, spaces=spaces,
                    my_facts=my, partner_facts=visible_facts(uid, p_uid, p_facts) if p_uid else [],
                    decisions=decs, conv=conv or {})
    if with_episodes and (space or query):
        q = f"{space['type'] if space else ''} {space.get('city', '') if space else ''} {query}".strip()
        try:
            snap.episodes = await recall(user["couple_id"], q, 3)
        except Exception:  # noqa
            snap.episodes = []
    snap.next = director(snap)
    return snap


async def _none():
    return None


ONBOARD_KEYS = ["partner_name", "how_met"]


def director(s: Snapshot) -> dict:
    """Return the single best next move. Keep goals tiny and human."""
    prof = s.user.get("profile") or {}
    conv = s.conv or {}
    turns = conv.get("turn_count", 0)
    cov = coverage(s.my_facts)
    first = (s.user.get("name") or "").split(" ")[0] or "there"
    pname = (s.partner or {}).get("name") or prof.get("partner_name")
    avoid = ["asking more than ONE question in a message",
             "listing many options in speech — show a widget instead",
             "repeating a question the user already answered (check TASTES and PROFILE first)"]
    nxt: dict = {"stage": "", "goal": "", "detail": {}, "avoid": avoid}

    if turns < 2 and not prof.get("greeted"):
        nxt.update(stage="welcome", goal=f"Warmly welcome {first}. Introduce yourself in one line and ask, lightly, what "
                   "they're celebrating or planning right now. Do NOT ask for dates, budget or tastes yet.")
        return nxt
    if not pname and turns < 12:
        nxt.update(stage="rapport", goal="Get to know them a little: casually ask their partner's name (then later, how they "
                   "met) and save it with remember_about_us. Keep it playful; if they want to jump into planning, let them.",
                   detail={"missing_profile": ["partner_name"]})
        if s.space is None:
            nxt["goal"] += " If they already said what they're planning, create the event space first."
        return nxt
    if s.space is None:
        nxt.update(stage="guide", goal="Find out what they want to plan next (wedding, engagement, prewedding, honeymoon, "
                   "a trip, or an anniversary/birthday) and create that event space as soon as they say it. Until then, "
                   "only chat, guide and answer questions about the app — no planning or recommendations.")
        return nxt
    sp_ = s.space
    if sp_.get("state") == "building":
        nxt.update(stage="building", goal="The plan is being woven in the background. Keep the conversation warm and light — "
                   "ask one small getting-to-know-you question or talk about what excites them. You'll be told when it's ready.")
        return nxt
    focus = sp.TEMPLATES[sp_["type"]]["taste_focus"]
    uncovered = [c for c in focus if cov.get(c, 0) < 2]
    streak = conv.get("taste_streak", 0)
    if sp_["missing_fields"]:
        f = sp_["missing_fields"][0]
        meta = sp.FIELD_META[f]
        nxt.update(stage="event_basics", goal=f"Ask ONLY for the {meta['label'].lower()} of their {sp_['title']} "
                   f"(field '{f}') in a natural way, then save it with update_event. If several details are still missing "
                   "and they're typing (not talking), you may instead offer the details form (ask_event_details).",
                   detail={"field": f, "remaining": sp_["missing_fields"]})
        if streak < 1 and uncovered and len(sp_["missing_fields"]) > 2 and turns % 3 == 2:
            nxt["goal"] += f" (Optional, for a change of pace: one quick taste question about {CATEGORIES[uncovered[0]]['label']}.)"
        return nxt
    if uncovered and streak < 2 and not (sp_.get("active_plan_version")):
        c = uncovered[0]
        nxt.update(stage="know_tastes", goal=f"Get to know {first}'s taste in {CATEGORIES[c]['label']} — this matters for "
                   f"their {sp_['title']}. Ask it like a friend would, and call show_taste_picker(category='{c}'). One category only.",
                   detail={"category": c, "uncovered": uncovered, "coverage": cov})
        return nxt
    if not s.partner and not prof.get("invite_offered"):
        nxt.update(stage="invite_partner", goal=f"Gently suggest inviting {pname or 'their partner'} so the plan is woven from "
                   "both tastes (call invite_partner if they agree). Mention it once only; don't block planning on it.")
        return nxt
    if not sp_.get("active_plan_version"):
        nxt.update(stage="ready_to_plan", goal=f"You know enough to start. Offer to weave their {sp_['title']} plan now; when they "
                   "agree call build_plan (it runs in the background — keep chatting while it builds).",
                   detail={"uncovered": uncovered})
        return nxt
    if sp_.get("state") == "stale":
        nxt.update(stage="refresh", goal="Event details changed since the plan was made. Offer to refresh the plan (build_plan).")
        return nxt
    days = None
    try:
        from datetime import date
        days = (date.fromisoformat(sp_.get("start_date", "")) - today()).days
    except ValueError:
        pass
    nxt.update(stage="refine", goal="The plan exists. Help them enjoy and refine it: highlight ONE section they haven't "
               "reacted to yet (show_plan_section), ask how it feels, and revise_plan on feedback. Also offer to-dos, "
               "budget tweaks, or companion help (partner insights, surprises).",
               detail={"days_to_event": days})
    return nxt


async def bump_taste_streak(uid: str, reset: bool = False):
    ref = db.document(f"conversations/{uid}")
    snap = await ref.get()
    cur = (snap.to_dict() or {}).get("taste_streak", 0) if snap.exists else 0
    await ref.set({"taste_streak": 0 if reset else cur + 1}, merge=True)


async def mark_stage_seen(uid: str, stage: str | None = None):
    """Once-only stages (welcome, invite suggestion) are marked after the agent has handled them."""
    if stage is None:
        stage = (await load(uid, with_episodes=False)).next.get("stage")
    flag = {"welcome": "greeted", "invite_partner": "invite_offered"}.get(stage)
    if flag:
        await db.document(f"users/{uid}").set({"profile": {flag: True}}, merge=True)
