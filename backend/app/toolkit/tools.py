"""All cupl product tools (published by the cupl MCP server)."""
import asyncio

from ..core.llm import gen_json
from ..db import db, list_col, new_id, now_iso
from ..services import calendar_svc, couple as couple_svc, dna as dna_svc, recommends_svc
from ..services import plan_engine, qloo, state, taste_intel
from ..services import spaces as sp
from ..services import tastes
from ..services.memory import recall, save_episode
from ..services.taste_intel import CATEGORIES, CATEGORY_NAMES
from .registry import ALL, GUIDE, PLANNER, SETUP, SPACE, obj, tool

S = {"type": "string"}
N = {"type": "number"}
B = {"type": "boolean"}
CAT = {"type": "string", "enum": CATEGORY_NAMES}
TYPES = list(sp.TEMPLATES)
DATE = {"type": "string", "description": "YYYY-MM-DD (convert phrases like '15th Feb' using TODAY)"}
EVENT_FIELDS = {
    "title": S, "city": S, "start_date": DATE, "end_date": DATE,
    "budget": {"type": "number", "description": "total in INR (25 lakh = 2500000)"},
    "guests": {"type": "integer"}, "ceremonies": {"type": "array", "items": S},
    "destination": S, "from_city": S, "travel_style": S, "mood": S, "occasion": S, "priorities": S,
}
APP_GUIDE = """cupl guide:
- Event Spaces: one per event (Prewedding, Engagement, Wedding, Honeymoon, Trip, Life Beyond). Each has its own plan, budget, to-dos, memories.
- Partner: invite from the Me page or ask me; they join with their own account so both tastes count.
- Tastes: tell me what you love or tap my suggestions. Each taste can be shared with your partner or kept private (eye icon on the Me page).
- Couple Taste DNA: what you both love, your unique flavours, and middle-ground ideas.
- Plans: woven from both your tastes with QLOO taste intelligence; every item shows 'Why this?'. Like, skip or mark done.
- Voice: tap the mic and talk to me; interrupt anytime.
- Memory: I remember tastes, decisions and experiences. See or delete them on the Me page.
- Surprises: plan surprises privately; your partner never sees them.
- I don't book vendors: I recommend and link to Maps so you book directly. Prices are estimates."""


def _brief(s: dict) -> dict:
    return {k: s.get(k) for k in ["id", "type", "title", "state", "city", "start_date", "end_date", "budget", "guests",
                                  "ceremonies", "destination", "missing_fields"] if s.get(k) not in (None, "", [])}


def _names(c):
    first = (c.user.get("name") or "").split(" ")[0]
    pname = (c.snap.partner or {}).get("name") or (c.user.get("profile") or {}).get("partner_name") or "their partner"
    return first, pname


# ============================== guidance / profile ==============================
@tool("get_next_step", "guidance", """What should I do next in this conversation? Returns the Director's ONE next move
(stage + goal) and a compact state summary. Call it whenever you're unsure what to do next, after big changes, or at the
start of a voice session.""")
async def get_next_step(c, a):
    s = c.snap
    return {"next": s.next, "mode": s.mode, "active_event": _brief(s.space) if s.space else None,
            "partner_joined": bool(s.partner), "taste_coverage": tastes.coverage(s.my_facts)}


@tool("app_help", "guidance", "How-to answers about using the cupl app (features, privacy, voice, partner invite).",
      obj({"topic": S}))
async def app_help(c, a):
    return {"guide": APP_GUIDE}


@tool("remember_about_us", "profile", """Save a personal or cultural detail the user shared, e.g. partner_name, how_met,
heritage, tradition, religion, country, state, hometown, culture, family_notes, nickname. Use this for life & heritage details, NOT for specific tastes.""",
      obj({"key": {"type": "string", "enum": ["partner_name", "how_met", "relationship_since", "hometown", "culture",
                                               "heritage", "tradition", "religion", "country", "state",
                                               "family_notes", "nickname", "love_language"]}, "value": S}, ["key", "value"]),
      mutates=True)
async def remember_about_us(c, a):
    await db.document(f"users/{c.uid}").set({"profile": {a["key"]: a["value"][:200]}}, merge=True)
    if c.user.get("couple_id") and a["key"] in ("heritage", "tradition", "religion", "culture", "state"):
        try:
            await dna_svc.compute(c.user["couple_id"])
        except Exception:
            pass
    return {"saved": {a["key"]: a["value"][:200]}}


@tool("update_my_name", "profile", "Update the user's display name (when they tell you what to call them).",
      obj({"name": S}, ["name"]), mutates=True)
async def update_my_name(c, a):
    name = a["name"].strip()[:40]
    if not name:
        return {"ok": False, "error": "empty name"}
    await db.document(f"users/{c.uid}").update({"name": name, "name_confirmed": True})
    return {"name": name}


@tool("set_love_status", "profile", "Set the couple's relationship phase.",
      obj({"status": {"type": "string", "enum": ["dating", "engaged", "married", "parents"]}}, ["status"]), mutates=True)
async def set_love_status(c, a):
    await db.document(f"couples/{c.user['couple_id']}").update({"status": a["status"]})
    return {"status": a["status"]}


@tool("invite_partner", "profile", "Create (or reuse) the partner invite link and show an invite card with copy/share buttons.",
      mutates=True)
async def invite_partner(c, a):
    if c.snap.partner:
        return {"ok": False, "error": f"{c.snap.partner.get('name')} has already joined."}
    inv = await couple_svc.create_invite(c.user)
    await db.document(f"users/{c.uid}").set({"profile": {"invite_offered": True}}, merge=True)
    return {"link": inv["link"], "widget": {"kind": "invite", "title": "Invite your partner", "link": inv["link"], "code": inv["code"]}}


# ============================== event spaces ==============================
@tool("list_events", "events", "List the couple's event spaces and which one is active.")
async def list_events(c, a):
    return {"events": [_brief(s) for s in c.snap.spaces], "active_id": c.user.get("active_space_id")}


@tool("create_event", "events", f"""Create a new event space and make it active. type: {', '.join(TYPES)}.
Pass any details the user ALREADY said (city, dates, budget...). Don't ask for details before creating it.""",
      obj({"type": {"type": "string", "enum": TYPES}, **EVENT_FIELDS}, ["type"]), mutates=True)
async def create_event(c, a):
    stype = a.pop("type")
    s, errors = await sp.create_space(c.user, stype, a)
    return {"created": _brief(s), "invalid": errors, "widget": {"kind": "refresh"}}

@tool("propose_plan", "events", """Propose a tentative plan or trip to the couple with a live brief card and a Save button on their screen.
Use this during conversations when the couple discusses a trip, celebration, birthday, or weekend escape, showing the tentative plan right on their screen so they can approve and save it to Our Plans.""",
      obj({"title": S, "type": {"type": "string", "enum": TYPES}, "city": S, "start_date": S, "end_date": S,
           "budget": S, "highlights": {"type": "array", "items": S}, "match_score": N}, ["title", "type", "highlights"]), mutates=True)
async def propose_plan(c, a):
    stype = a.get("type", "trip")
    s, errors = await sp.create_space(c.user, stype, {
        "title": a["title"],
        "city": a.get("city"),
        "start_date": a.get("start_date"),
        "end_date": a.get("end_date"),
    })
    dates_str = f"{a.get('start_date', '')} to {a.get('end_date', '')}".strip(" to")
    return {
        "proposed": a["title"],
        "space_id": s["id"],
        "widget": {
            "kind": "plan_proposal",
            "title": a["title"],
            "plan_type": stype,
            "city": a.get("city", ""),
            "dates": dates_str,
            "budget": a.get("budget", ""),
            "highlights": a.get("highlights", []),
            "match_score": a.get("match_score", 0.95),
            "space_id": s["id"],
        }
    }



@tool("save_cultural_roots", "profile", """Save cultural roots, heritage, and faith/traditions for the user/couple.
These power QLOO Cultural Intelligence to weave regional rituals, ceremonies, and traditional aesthetics authentically into plans.""",
      obj({"heritage": {"type": "string", "description": "e.g. Maharashtrian, Bengali, Punjabi, Gujarati, South Indian, Marwari, Cross-cultural"},
           "tradition": {"type": "string", "description": "e.g. Hindu, Sikh, Christian, Muslim, Jain, Inter-faith, Secular"},
           "state": {"type": "string", "description": "home state or city, e.g. Maharashtra, Kolkata, Punjab, Delhi"},
           "country": {"type": "string", "description": "country, default India"}}, ["heritage"]), mutates=True)
async def save_cultural_roots(c, a):
    prof_upd = {}
    for k in ("heritage", "tradition", "state", "country"):
        if a.get(k):
            prof_upd[k] = str(a[k]).strip()[:60]
    if prof_upd:
        await db.document(f"users/{c.uid}").set({"profile": prof_upd}, merge=True)
        if c.user.get("couple_id"):
            try:
                await dna_svc.compute(c.user["couple_id"])
            except Exception as e:
                log.warning("DNA recompute failed: %s", e)
    return {"saved": prof_upd, "note": "Cultural roots saved. QLOO cultural intelligence is now tailored to their traditions."}


@tool("update_event", "events", "Save details of the ACTIVE event space (one or many fields). Validation errors are returned.",
      obj(EVENT_FIELDS), modes=SPACE, mutates=True)
async def update_event(c, a):
    target_space = c.space
    if not target_space:
        if c.snap.spaces:
            target_space = c.snap.spaces[0]
        else:
            return {"error": "No active event space found. Please create an event first with create_event."}
    s, errors = await sp.update_space(target_space["id"], c.user["couple_id"], a)
    await state.bump_taste_streak(c.uid, reset=True)
    res = {"event": _brief(s), "invalid": errors, "widget": {"kind": "refresh"}}
    if a.get("start_date"):
        conflict = await sp.check_schedule_conflict(c.user["couple_id"], a["start_date"], a.get("end_date"), exclude_sid=target_space["id"])
        if conflict:
            res["schedule_note"] = f"Heads up: These dates overlap with your existing event '{conflict['event_title']}' ({conflict['dates']}). Mention this warmly to confirm their schedule."
    return res


@tool("switch_event", "events", "Make another event space active (by id from list_events).",
      obj({"event_id": S}, ["event_id"]), mutates=True)
async def switch_event(c, a):
    s = await sp.get_space(a["event_id"], c.user["couple_id"])
    await db.document(f"users/{c.uid}").update({"active_space_id": s["id"]})
    return {"active": _brief(s), "widget": {"kind": "refresh"}}


@tool("ask_event_details", "events", """Show an interactive form in chat for the active event's missing details.
Use in text chat when 2+ details are missing, or when the user prefers a form. In voice, ask conversationally instead.""",
      modes=SPACE)
async def ask_event_details(c, a):
    s = c.space
    specs = sp.field_specs(s["type"], s["missing_fields"] or None)
    for f in specs:
        f["value"] = s.get(f["key"])
    return {"shown": "details form", "widget": {"kind": "space_form", "title": f"{s['title']} details", "space_id": s["id"], "fields": specs}}


# ============================== tastes (taste intelligence + QLOO) ==============================
@tool("remember_tastes", "tastes", """THE way to record tastes the user expresses in words. Pass the user's own words
verbatim in `text` (e.g. "I like Arijit Singh and hate loud DJs"). The server's taste-intelligence pipeline extracts each
taste, decides its category, and grounds it to the exact QLOO entity. Never map names to categories or IDs yourself.
If a name is ambiguous it returns needs_clarification and shows the user a 'which one?' card.""",
      obj({"text": S, "category_hint": {**CAT, "description": "category you just asked about, if any"},
           "visibility": {"type": "string", "enum": ["shared", "private"]}}, ["text"]), mutates=True)
async def remember_tastes(c, a):
    first, pname = _names(c)
    items = await taste_intel.extract(a["text"], first or "the user", pname, a.get("category_hint"))
    if not items:
        return {"saved": [], "note": "No concrete taste found in that text."}
    p_uid = (c.snap.partner or {}).get("id")
    mine = list(c.snap.my_facts)
    res_all = await asyncio.gather(*[taste_intel.resolve(i["mention"], i["category"], i["kind"], i.get("context_hint") or "")
                                     for i in items])
    saved, unclear, widgets = [], [], []
    for it, res in zip(items, res_all):
        if res["status"] == "ambiguous":
            unclear.append({"mention": it["mention"], "options": [x["label"] for x in res["candidates"]]})
            widgets.append({"kind": "disambiguation", "title": f"Which “{it['mention']}” did you mean?",
                            "category": res["category"], "sentiment": it["sentiment"], "about": it["about"],
                            "mention": it["mention"], "options": res["candidates"]})
            continue
        if it["about"] == "partner":
            if p_uid:
                await tastes.save_resolution(p_uid, res, it["sentiment"], 0.4, "hint", "private")
            else:
                await db.document(f"users/{c.uid}").set({"profile": {"partner_hints": (c.user.get("profile") or {}).get(
                    "partner_hints", [])[-20:] + [f"{res['category']}: {res.get('name') or it['mention']}"]}}, merge=True)
            saved.append({"about": "partner", "name": res.get("name") or it["mention"], "category": res["category"]})
            continue
        await tastes.save_resolution(c.uid, res, it["sentiment"], max(0.7, it["confidence"]), "chat",
                                     a.get("visibility", "shared"), existing=mine)
        saved.append({"name": res.get("name") or it["mention"], "category": res["category"],
                      "feeling": "likes" if it["sentiment"] > 0 else "dislikes", "grounded_in_qloo": res["status"] == "resolved"})
    return {"saved": saved, "needs_clarification": unclear, "widgets": widgets}


@tool("show_taste_picker", "tastes", """Show an interactive taste picker with LIVE suggestions (partner's shared picks 💞 +
QLOO recommendations) for ONE category, with search and 'add your own'. Use it whenever you ask about a taste.
Say one short friendly line with it; then wait for their picks.""",
      obj({"category": CAT, "title": {"type": "string", "description": "friendly title, e.g. 'Singers you could listen to all day'"},
           "sentiment": {"type": "string", "enum": ["like", "dislike"]}}, ["category", "title"]), modes=SPACE)
async def show_taste_picker(c, a):
    p = c.snap.partner
    sugg = await tastes.suggest(a["category"], c.uid, (p or {}).get("id"), (c.space or {}).get("city"),
                                c.snap.my_facts, c.snap.partner_facts)
    await state.bump_taste_streak(c.uid)
    return {"suggested": [s["name"] for s in sugg][:8],
            "widget": {"kind": "taste_picker", "title": a["title"], "category": a["category"],
                       "sentiment": a.get("sentiment", "like"), "searchable": bool(CATEGORIES[a["category"]]["types"]),
                       "multi": True, "max": 6, "suggestions": sugg}}


@tool("get_tastes", "tastes", "Get the user's saved tastes (and partner's SHARED tastes) grouped by category.")
async def get_tastes(c, a):
    def group(fs):
        out = {}
        for f in fs:
            out.setdefault(f["category"], []).append(("✗ " if f.get("sentiment", 0) < 0 else "") + f["text"])
        return out
    return {"mine": group(c.snap.my_facts), "partner_shared": group(c.snap.partner_facts),
            "partner_name": (c.snap.partner or {}).get("name")}


@tool("qloo_search", "qloo", "Look up real entities in QLOO by name within a category (for checking a name exists or showing options).",
      obj({"query": S, "category": CAT}, ["query", "category"]), modes=SPACE)
async def qloo_search(c, a):
    types = CATEGORIES[a["category"]]["types"]
    if not types:
        return {"results": [], "note": "This category has no QLOO entity type; treat as free text."}
    res = await qloo.search(a["query"], types, take=6)
    return {"results": [{"name": r["name"], "entity_id": r["entity_id"], "year": r.get("year"),
                         "type": (r["types"] or [""])[0].split(":")[-1]} for r in res]}


@tool("qloo_recommend", "qloo", """Ad-hoc taste-based recommendations from QLOO, blended for the couple (or one partner).
IMPORTANT RULES:
- For wedding/trip destinations (e.g. European destination, honeymoon, wedding city): use category="travel" (urn:entity:destination). NEVER use 'place' for destinations!
- For venues, restaurants, cafes in a specific city: use category="place" with location.
- For music/songs: use category="music".
Shows cards in chat. For full event plans use build_plan instead.""",
      obj({"category": {"type": "string", "enum": [k for k, v in CATEGORIES.items() if v["types"]]},
           "location": {"type": "string", "description": "city/area; required for 'place' category"},
           "for_whom": {"type": "string", "enum": ["couple", "me", "partner"]},
           "title": S}, ["category"]), modes=SPACE)
async def qloo_recommend(c, a):
    qtype = CATEGORIES[a["category"]]["types"][0]
    loc = a.get("location") or (c.space or {}).get("city") or (c.space or {}).get("destination")
    if qtype == qloo.PLACE and not loc:
        return {"ok": False, "error": "Ask which city/area first."}
    who = a.get("for_whom", "couple")
    sig = {}
    if who in ("couple", "me"):
        sig[c.uid] = tastes.signals(c.snap.my_facts)
    if who in ("couple", "partner") and c.snap.partner:
        sig[c.snap.partner["id"]] = tastes.signals(c.snap.partner_facts)
    excl = tastes.disliked_ids(c.snap.my_facts)
    res = await qloo.blend(qtype, sig, loc, 8, excl)
    items = [{"id": new_id("i"), "title": r["name"], "image": r.get("image"), "loved_by_both": r.get("loved_by_both"),
              "affinity": r.get("affinity"), "why": [", ".join(r.get("tags", [])[:3])] if r.get("tags") else [],
              "maps_url": ("https://www.google.com/maps/search/?api=1&query=" + f"{r['name']} {loc}".replace(" ", "+"))
              if qtype == qloo.PLACE else None} for r in res[:6]]
    return {"results": [{"name": i["title"], "loved_by_both": i["loved_by_both"], "tags": r.get("tags", [])[:3]}
                        for i, r in zip(items, res)],
            "widget": {"kind": "recs", "title": a.get("title") or "Picked for you two", "items": items}}


# ============================== couple DNA ==============================
@tool("get_couple_dna", "dna", "Compute & show the Couple Taste DNA: shared loves, unique flavours, differences with middle-ground ideas, vibe.",
      modes=SPACE)
async def get_couple_dna(c, a):
    d = await dna_svc.compute(c.user["couple_id"])
    return {"vibe": d["vibe"], "shared": [s["name"] for s in d["shared"]][:15],
            "differences": [{"category": x["category"], "middle_ground": x["middle_ground"]} for x in d["differences"]],
            "widget": {"kind": "dna", "title": "Your Couple Taste DNA", "dna": d}}


# ============================== plans ==============================
@tool("build_plan", "plan", """Start weaving the full plan for the active event (both partners' tastes + QLOO + planner).
Runs in the BACKGROUND (30-90s) and returns immediately. Keep the conversation going; you'll get a [PLAN READY] event.""",
      modes={PLANNER}, mutates=True, slow=False)
async def build_plan(c, a):
    s = c.space
    if s.get("state") == "building" or plan_engine.is_building(s["id"]):
        return {"status": "already_building"}
    started = await plan_engine.start_build(s["id"], None, None, c.uid)
    await state.bump_taste_streak(c.uid, reset=True)
    return {"status": "started" if started else "already_building", "widget": {"kind": "plan_progress", "space_id": s["id"], "title": s["title"]},
            "note": "Building in background. Say something warm and keep chatting (one light question)."}


@tool("get_plan", "plan", "Get the current plan of the active event: section keys, titles, item names & statuses, budget split.",
      modes={PLANNER})
async def get_plan(c, a):
    plan = await plan_engine.latest_plan(c.space, include_building=True)
    if not plan:
        return {"plan": None, "note": "No plan yet — offer build_plan."}
    return {"status": plan.get("status"), "sections": [
        {"key": s["key"], "title": s["title"], "status": s.get("status"), "error": s.get("error"),
         "items": [f"{i['title']} ({i.get('status')})" for i in s.get("items", [])]} for s in plan["sections"]],
        "budget": plan.get("budget")}


@tool("revise_plan", "plan", """Revise the plan following the user's feedback (e.g. 'no loud DJs, more Sufi', 'cheaper venues').
Pass section_keys (from get_plan) to touch only those sections; omit to revise everything. Runs in background.""",
      obj({"instruction": S, "section_keys": {"type": "array", "items": S}}, ["instruction"]), modes={PLANNER}, mutates=True)
async def revise_plan(c, a):
    s = c.space
    if plan_engine.is_building(s["id"]):
        return {"status": "already_building", "note": "A build is running; try again when it's ready."}
    await db.document(f"couples/{c.user['couple_id']}/decisions/{new_id('d')}").set(
        {"summary": a["instruction"][:300], "by_uid": c.uid, "space_id": s["id"], "at": now_iso()})
    await plan_engine.start_build(s["id"], a.get("section_keys"), a["instruction"], c.uid)
    return {"status": "started", "widget": {"kind": "plan_progress", "space_id": s["id"], "title": s["title"]}}


@tool("show_plan_section", "plan", "Show one plan section's recommendation cards in chat (key from get_plan).",
      obj({"section_key": S}, ["section_key"]), modes={PLANNER})
async def show_plan_section(c, a):
    plan = await plan_engine.latest_plan(c.space)
    sec = next((s for s in (plan or {}).get("sections", []) if s["key"] == a["section_key"]), None)
    if not sec:
        return {"ok": False, "error": "Section not found; call get_plan for valid keys."}
    return {"items": [i["title"] for i in sec["items"]], "summary": sec.get("summary"),
            "widget": {"kind": "recs", "title": sec["title"], "space_id": c.space["id"], "items": sec["items"]}}


@tool("set_budget_split", "plan", "Set the budget split (percentages per category) for the active plan.",
      obj({"allocations": {"type": "array", "items": obj({"category": S, "pct": N}, ["category", "pct"])}}, ["allocations"]),
      modes={PLANNER}, mutates=True)
async def set_budget_split(c, a):
    return await plan_engine.set_budget(c.space, a["allocations"])


# ============================== to-dos & reminders ==============================
@tool("add_todo", "todos", "Add a to-do to the active event.", obj({"title": S, "due": DATE}, ["title"]), modes=SPACE, mutates=True)
async def add_todo(c, a):
    await db.document(f"spaces/{c.space['id']}/todos/{new_id('t')}").set(
        {"title": a["title"][:200], "due": a.get("due"), "done": False, "assignee": None, "source": "agent", "created_at": now_iso()})
    return {"added": a["title"], "widget": {"kind": "refresh"}}


@tool("list_todos", "todos", "List to-dos of the active event.", modes=SPACE)
async def list_todos(c, a):
    t = await list_col(db.collection(f"spaces/{c.space['id']}/todos"))
    t.sort(key=lambda x: (x.get("done", False), x.get("due") or "9999"))
    return {"todos": [{"title": x["title"], "due": x.get("due"), "done": x.get("done")} for x in t]}


@tool("complete_todo", "todos", "Mark a to-do done (fuzzy title match).", obj({"title": S}, ["title"]), modes=SPACE, mutates=True)
async def complete_todo(c, a):
    q = a["title"].lower()
    for t in await list_col(db.collection(f"spaces/{c.space['id']}/todos")):
        if q in t["title"].lower() or taste_intel.name_similarity(q, t["title"]) > 0.7:
            await db.document(f"spaces/{c.space['id']}/todos/{t['id']}").update({"done": True})
            return {"done": t["title"], "widget": {"kind": "refresh"}}
    return {"ok": False, "error": "To-do not found; call list_todos."}


@tool("set_reminder", "todos", "Schedule an in-app reminder for the user.",
      obj({"text": S, "at": {"type": "string", "description": "ISO datetime with timezone, e.g. 2026-11-02T10:00:00+05:30"}},
          ["text", "at"]), modes=SPACE)
async def set_reminder(c, a):
    await db.document(f"reminders/{new_id('r')}").set(
        {"uid": c.uid, "text": a["text"][:200], "at": a["at"], "sent": False, "created_at": now_iso()})
    return {"scheduled": a["at"]}


# ============================== memory ==============================
@tool("recall_memories", "memory", "Search the couple's past experiences, decisions and memories (semantic).",
      obj({"query": S}, ["query"]))
async def recall_memories(c, a):
    eps = await recall(c.user["couple_id"], a["query"], 4)
    return {"memories": [{"summary": e.get("summary"), "loved": e.get("highlights"), "disliked": e.get("lowlights")} for e in eps],
            "decisions": [d["summary"] for d in c.snap.decisions[:8]]}


@tool("save_memory", "memory", "Save how a past event/trip/date went (an experience memory used to personalise future plans).",
      obj({"summary": S, "rating": {"type": "number", "minimum": 1, "maximum": 5}, "highlights": {"type": "array", "items": S},
           "lowlights": {"type": "array", "items": S}}, ["summary"]), modes=SPACE)
async def save_memory(c, a):
    e = await save_episode(c.user["couple_id"], a["summary"], (c.space or {}).get("id"), a.get("rating"),
                           a.get("highlights"), a.get("lowlights"), c.uid)
    return {"saved": e["summary"]}


# ============================== companion ==============================
@tool("partner_insight", "companion", """What does the partner love? Returns the partner's SHARED tastes + shared couple loves,
to answer 'what would Priya love for dinner?' or gift questions. Never reveals private tastes.""",
      obj({"question": S}), modes=SPACE)
async def partner_insight(c, a):
    p = c.snap.partner
    if not p:
        hints = (c.user.get("profile") or {}).get("partner_hints", [])
        return {"ok": False, "error": "Partner hasn't joined yet — offer invite_partner.", "what_you_told_me": hints}
    fs = c.snap.partner_facts
    dna = c.snap.couple.get("dna") or {}
    return {"partner": p.get("name"), "loves": [f"{f['category']}: {f['text']}" for f in fs if f.get("sentiment", 0) > 0][:40],
            "dislikes": [f"{f['category']}: {f['text']}" for f in fs if f.get("sentiment", 0) < 0][:15],
            "shared_loves": [s["name"] for s in dna.get("shared", [])][:12]}


@tool("create_surprise", "companion", """Plan a PRIVATE surprise for the partner (only the requester ever sees it). Uses the
partner's shared tastes + QLOO. Never mention surprises to the other partner.""",
      obj({"occasion": S, "date": DATE, "notes": S}, ["occasion"]), modes=SPACE, slow=True)
async def create_surprise(c, a):
    p = c.snap.partner
    if not p:
        return {"ok": False, "error": "Partner hasn't joined yet."}
    fs = c.snap.partner_facts
    sig = tastes.signals(fs, 12)
    loc = (c.space or {}).get("city")
    calls = [qloo.insights(qloo.BRAND, sig["entities"], sig["tags"], take=8), qloo.insights(qloo.ARTIST, sig["entities"], sig["tags"], take=6)]
    if loc:
        calls.append(qloo.insights(qloo.PLACE, sig["entities"], sig["tags"], loc, take=10))
    res = await asyncio.gather(*calls, return_exceptions=True)
    cands = [f"{e['name']} ({kind})" for r, kind in zip(res, ["brand", "artist", "place"]) if not isinstance(r, Exception) for e in r]
    data = await gen_json(
        f"Plan a surprise for {p.get('name')} for: {a['occasion']} {a.get('date', '')}. Notes: {a.get('notes', '')}.\n"
        f"Their loves: {[f['text'] for f in fs if f.get('sentiment', 0) > 0][:30]}\nTaste-intelligence candidates: {cands}\n"
        "Give 4-5 specific surprise ideas (experience, gift, music moment, place) using candidates where relevant; each with why.",
        {"type": "OBJECT", "properties": {"ideas": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
            "title": S, "description": S, "why": S}, "required": ["title", "description", "why"]}}}, "required": ["ideas"]},
        temperature=0.7)
    doc = {"owner_uid": c.uid, "couple_id": c.user["couple_id"], "for_name": p.get("name"), "occasion": a["occasion"],
           "date": a.get("date"), "notes": a.get("notes"), "ideas": data.get("ideas", []), "created_at": now_iso()}
    await db.document(f"surprises/{new_id('sp')}").set(doc)
    return {"ideas": [i["title"] for i in doc["ideas"]], "private": True,
            "widget": {"kind": "surprise", "title": f"🤫 Surprise for {p.get('name')}", "ideas": doc["ideas"]}}


# ============================== conversational UI ==============================
@tool("show_choices", "ui", "Show 2-6 tappable options for a question (single or multi select).",
      obj({"title": S, "options": {"type": "array", "items": S, "minItems": 2, "maxItems": 6}, "multi": B}, ["title", "options"]))
async def show_choices(c, a):
    return {"shown": True, "widget": {"kind": "choices", "title": a["title"], "options": a["options"], "multi": bool(a.get("multi"))}}


@tool("confirm_action", "ui", "Ask the user to confirm a major change (Yes/No buttons). Wait for their answer before acting.",
      obj({"summary": S}, ["summary"]))
async def confirm_action(c, a):
    return {"shown": True, "widget": {"kind": "confirm", "title": a["summary"]}}


# ============================== Everyday Couple Plans & Recommendations ==============================
@tool("add_couple_plan", "plans", """Add an everyday couple plan to the couple's Plans tab and unified Calendar (e.g. movie streaming night, romantic dinner, spontaneous 2-day getaway, or couple experience).
Takes: title, category (movie, dining, travel, cocktail, decor, music, experience), date (YYYY-MM-DD), time (e.g. '8:00 PM'), description, maps_url (optional), is_private (optional).
Call this whenever the couple agrees on an everyday date, movie night, dinner reservation, or getaway to schedule.""",
      obj({"title": S, "category": {"type": "string", "enum": ["movie", "dining", "travel", "cocktail", "decor", "music", "experience"]},
           "date": DATE, "time": S, "description": S, "maps_url": S, "is_private": B}, ["title", "category", "date"]), mutates=True)
async def add_couple_plan(c, a):
    item = await calendar_svc.add_calendar_item(c.user, {
        "title": a["title"],
        "category": a.get("category", "dining"),
        "date": a["date"],
        "time": a.get("time"),
        "description": a.get("description", ""),
        "maps_url": a.get("maps_url"),
        "is_private": a.get("is_private", False),
    })
    return {
        "ok": True,
        "plan_id": item.get("id"),
        "title": a["title"],
        "date": a["date"],
        "message": f"Added '{a['title']}' to your couple Plans and Calendar for {a['date']} ✨"
    }


@tool("get_lifestyle_recommends", "recommends", """Fetch the couple's active curated lifestyle recommendations (Friday night movies, weekend dining, signature cocktails, living room decor, spontaneous getaways) tailored to their Couple Taste DNA and life-stage.
Call this when the user asks for recommendations, date night ideas, movie suggestions, or weekend escapes.""",
      obj({}, []))
async def get_lifestyle_recommends(c, a):
    recs = await recommends_svc.get_lifestyle_recommendations(c.user)
    return {
        "couple_vibe": recs.get("couple_vibe"),
        "active_city": recs.get("active_city"),
        "couple_status": recs.get("couple_status"),
        "recommendations": [
            {
                "id": r["id"],
                "category": r["category"],
                "category_label": r.get("category_label"),
                "title": r["title"],
                "subtitle": r.get("subtitle"),
                "affinity": r.get("affinity"),
                "description": r.get("description"),
                "why": r.get("why"),
                "suggested_date": r.get("suggested_date"),
                "est_cost": r.get("est_cost"),
                "maps_url": r.get("maps_url"),
            }
            for r in recs.get("couple_recs", [])[:4]
        ]
    }
