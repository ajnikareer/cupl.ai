import os

def patch_spaces():
    path = "backend/app/services/spaces.py"
    with open(path, "r", encoding="utf-8") as f:
        c = f.read().replace("\r\n", "\n")

    conflict_func = '''async def check_schedule_conflict(couple_id: str, start_date: str, end_date: str | None = None, exclude_sid: str | None = None) -> dict | None:
    """Detect if proposed dates overlap with an existing event space for this couple."""
    if not start_date:
        return None
    try:
        s_new = date.fromisoformat(start_date[:10])
        e_new = date.fromisoformat(end_date[:10]) if end_date else s_new
    except (ValueError, TypeError):
        return None

    existing = await list_spaces(couple_id)
    for sp in existing:
        if exclude_sid and sp["id"] == exclude_sid:
            continue
        s_str = sp.get("start_date")
        if not s_str:
            continue
        try:
            s_cur = date.fromisoformat(s_str[:10])
            e_cur = date.fromisoformat(sp["end_date"][:10]) if sp.get("end_date") else s_cur
        except (ValueError, TypeError):
            continue

        if max(s_new, s_cur) <= min(e_new, e_cur):
            d_str = f"{s_cur.isoformat()} to {e_cur.isoformat()}" if s_cur != e_cur else s_cur.isoformat()
            return {
                "conflict": True,
                "event_id": sp["id"],
                "event_title": sp["title"],
                "event_type": sp["type"],
                "dates": d_str,
            }
    return None


'''
    target = 'async def create_space(user: dict,'
    assert target in c, "target in spaces.py not found"
    c = c.replace(target, conflict_func + target)

    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("Patched spaces.py with check_schedule_conflict.")

def patch_tools():
    path = "backend/app/toolkit/tools.py"
    with open(path, "r", encoding="utf-8") as f:
        c = f.read().replace("\r\n", "\n")

    old_update = """async def update_event(c, a):
    target_space = c.space
    if not target_space:
        if c.snap.spaces:
            target_space = c.snap.spaces[0]
        else:
            return {"error": "No active event space found. Please create an event first with create_event."}
    s, errors = await sp.update_space(target_space["id"], c.user["couple_id"], a)
    await state.bump_taste_streak(c.uid, reset=True)
    return {"event": _brief(s), "invalid": errors, "widget": {"kind": "refresh"}}"""

    new_update = """async def update_event(c, a):
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
    return res"""

    assert old_update in c, "old_update not found in tools.py"
    c = c.replace(old_update, new_update)

    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("Patched tools.py with conflict checking in update_event.")

def patch_context():
    path = "backend/app/agent/context.py"
    with open(path, "r", encoding="utf-8") as f:
        c = f.read().replace("\r\n", "\n")

    target = "    if s.space:\n        sp_ = s.space"
    timeline_code = """    timeline = []
    for x in s.spaces:
        if x.get("start_date"):
            d_range = x["start_date"] + (f" to {x['end_date']}" if x.get("end_date") else "")
            timeline.append(f"{x['title']} ({x['type']}): {d_range} in {x.get('city') or x.get('destination') or 'TBD'}")
    if timeline:
        lines.append("COUPLE SCHEDULE & TIMELINE (check for conflicts when dates are discussed): " + " | ".join(timeline))

    if s.space:
        sp_ = s.space"""

    assert target in c, "target in context.py not found"
    c = c.replace(target, timeline_code)

    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("Patched context.py with couple schedule & timeline context.")

def patch_plan_engine():
    path = "backend/app/services/plan_engine.py"
    with open(path, "r", encoding="utf-8") as f:
        c = f.read().replace("\r\n", "\n")

    old_target = """        if not candidates:
            sec["error"] = "No strong matches found yet. Share a few more tastes and refresh."
            return sec"""

    new_filter = """        if not candidates:
            sec["error"] = "No strong matches found yet. Share a few more tastes and refresh."
            return sec

        if spec["qtype"] == qloo.PLACE and space.get("type") in ("wedding", "prewedding", "engagement", "honeymoon"):
            UNSUITABLE_CHAINS = ("collection o", "capital o", "fabhotel", "oyo", "motel", "hostel", "dorm", "lodge", "budget inn")
            CELEBRATION_PRIORITY = ("palace", "resort", "heritage", "fort", "villa", "garden", "boutique", "haveli", "chateau", "castle", "luxury", "estate", "retreat", "taj", "oberoi", "itc", "leela", "marriott", "hyatt")
            def _venue_rank(x):
                nm = (x.get("name") or "").lower()
                tgs = " ".join(x.get("tags") or []).lower()
                score = x.get("affinity") or 0.5
                if any(u in nm for u in UNSUITABLE_CHAINS):
                    score -= 0.45
                if any(p in nm or p in tgs for p in CELEBRATION_PRIORITY):
                    score += 0.25
                return score
            candidates.sort(key=_venue_rank, reverse=True)"""

    assert old_target in c, "old_target not found in plan_engine.py"
    c = c.replace(old_target, new_filter)

    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("Patched plan_engine.py with global celebration venue ranking.")

def patch_state():
    path = "backend/app/services/state.py"
    with open(path, "r", encoding="utf-8") as f:
        c = f.read().replace("\r\n", "\n")

    old_welc = """    # 1. Partner Onboarding (Bride joining Groom's existing space)
    is_joining_partner = s.partner is not None and len(s.my_facts) < 3 and not prof.get("partner_welcomed")
    if is_joining_partner and turns < 4:
        sp_title = s.space["title"] if s.space else "celebration"
        sp_loc = f" in {s.space['city']}" if s.space and s.space.get("city") else ""
        nxt.update(stage="welcome_partner", goal=f"Warmly welcome {first} to WeaveWed as {pname}'s partner! "
                   f"Tell {first} excitedly: '{pname} has already started weaving your couple space for {sp_title}{sp_loc}! "
                   f"Now it is your turn to shape the celebration so it reflects your personal heart and aesthetic.' "
                   f"1) Immediately save any tastes {first} shared with remember_tastes. "
                   f"2) Ask about their cultural heritage & traditions ('What cultural roots or wedding traditions are you honoring — e.g. Maharashtrian, Bengali, Punjabi, Hindu, Sikh, interfaith?'). "
                   f"3) Save it with save_cultural_roots. Do NOT ask 'what are you celebrating or planning' because the event space already exists.")
        return nxt"""

    new_welc = """    # 1. Partner Onboarding (Warm, individual-first, empowering)
    is_joining_partner = s.partner is not None and len(s.my_facts) < 3 and not prof.get("partner_welcomed")
    if is_joining_partner and turns < 4:
        sp_title = s.space["title"] if s.space else "celebration"
        sp_loc = f" in {s.space['city']}" if s.space and s.space.get("city") else ""
        nxt.update(stage="welcome_partner", goal=f"Warmly welcome {first} to WeaveWed as an individual co-creator with {pname}! "
                   f"Treat {first} with genuine excitement: 'Welcome, {first}! I\\'m here to make sure your individual aesthetic, favorite music, and style take center stage.' "
                   f"Mention gently that {pname} and {first} are linked with a {sp_title}{sp_loc} in progress, but emphasize that before touching that, you want to get to know {first}'s personal vibe. "
                   f"1) Save any tastes {first} shares with remember_tastes. "
                   f"2) Ask about {first}'s cultural heritage & wedding traditions (save_cultural_roots). "
                   f"Do NOT make {first} feel like a secondary guest or lecture them on what their partner did.")
        return nxt"""

    assert old_welc in c, "old_welc not found in state.py"
    c = c.replace(old_welc, new_welc)

    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("Patched state.py with empowering individual-first partner onboarding.")

if __name__ == "__main__":
    patch_spaces()
    patch_tools()
    patch_context()
    patch_plan_engine()
    patch_state()
    print("ALL PENDING FIXES APPLIED SUCCESSFULLY!")

