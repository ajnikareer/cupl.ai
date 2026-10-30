import os
import sys

def patch_auth():
    path = "backend/app/auth.py"
    with open(path, "r", encoding="utf-8") as f:
        c = f.read().replace("\r\n", "\n")
    
    # Replace line 21 fallback
    target = 'name = "Narayan" if "narayan" in token.lower() else ("Amruta" if "amruta" in token.lower() else "Priya")'
    replacement = 'clean_uid = uid.split("@")[0].split(".")[0].replace("_", " ").replace("-", " ")\n        name = "Narayan" if "narayan" in token.lower() else ("Amruta" if "amruta" in token.lower() else clean_uid.title())'
    assert target in c, "target in auth.py not found"
    c = c.replace(target, replacement)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("Patched auth.py successfully.")

def patch_spaces():
    path = "backend/app/services/spaces.py"
    with open(path, "r", encoding="utf-8") as f:
        c = f.read().replace("\r\n", "\n")
    
    old_create = """async def create_space(user: dict, stype: str, fields: dict) -> tuple[dict, list[str]]:
    if stype not in TEMPLATES:
        raise HTTPException(400, f"Unknown event type '{stype}'. Use one of {list(TEMPLATES)}")
    f, errors = clean_fields(fields, stype)
    sid = new_id("s")
    space = {"couple_id": user["couple_id"], "type": stype, "title": f.pop("title", None) or TEMPLATES[stype]["label"],
             "currency": "INR", "created_by": user["uid"], "created_at": now_iso(), "active_plan_version": 0,
             "building_version": None, "excluded_ids": [], **f}
    space["state"] = compute_state(space)
    await db.document(f"spaces/{sid}").set(space)
    await db.document(f"users/{user['uid']}").update({"active_space_id": sid})
    user["active_space_id"] = sid
    space["id"] = sid
    return public(space), errors"""

    new_create = """async def create_space(user: dict, stype: str, fields: dict) -> tuple[dict, list[str]]:
    if stype not in TEMPLATES:
        raise HTTPException(400, f"Unknown event type '{stype}'. Use one of {list(TEMPLATES)}")
    f, errors = clean_fields(fields, stype)
    title = f.pop("title", None) or TEMPLATES[stype]["label"]

    # Deduplication: reuse/activate existing space of same type or title
    existing = await list_spaces(user["couple_id"])
    match = next((s for s in existing if s.get("type") == stype or s.get("title", "").strip().lower() == title.strip().lower()), None)
    if match:
        sid = match["id"]
        if f:
            await update_space(sid, user["couple_id"], f)
            match = await get_space(sid, user["couple_id"])
        await db.document(f"users/{user['uid']}").update({"active_space_id": sid})
        user["active_space_id"] = sid
        return public(match), errors

    sid = new_id("s")
    space = {"couple_id": user["couple_id"], "type": stype, "title": title,
             "currency": "INR", "created_by": user["uid"], "created_at": now_iso(), "active_plan_version": 0,
             "building_version": None, "excluded_ids": [], **f}
    space["state"] = compute_state(space)
    await db.document(f"spaces/{sid}").set(space)
    await db.document(f"users/{user['uid']}").update({"active_space_id": sid})
    user["active_space_id"] = sid
    space["id"] = sid
    return public(space), errors"""

    assert old_create in c, "old_create not found in spaces.py"
    c = c.replace(old_create, new_create)
    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("Patched spaces.py successfully.")

def patch_tools():
    path = "backend/app/toolkit/tools.py"
    with open(path, "r", encoding="utf-8") as f:
        c = f.read().replace("\r\n", "\n")

    # 1. Add save_cultural_roots tool before update_event
    roots_tool = '''@tool("save_cultural_roots", "profile", """Save cultural roots, heritage, and faith/traditions for the user/couple.
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


'''
    target_event = '@tool("update_event", "events",'
    assert target_event in c, "target_event not found in tools.py"
    c = c.replace(target_event, roots_tool + target_event)

    # 2. Guard update_event against c.space is None
    old_update_fn = """async def update_event(c, a):
    s, errors = await sp.update_space(c.space["id"], c.user["couple_id"], a)
    await state.bump_taste_streak(c.uid, reset=True)
    return {"event": _brief(s), "invalid": errors, "widget": {"kind": "refresh"}}"""

    new_update_fn = """async def update_event(c, a):
    target_space = c.space
    if not target_space:
        if c.snap.spaces:
            target_space = c.snap.spaces[0]
        else:
            return {"error": "No active event space found. Please create an event first with create_event."}
    s, errors = await sp.update_space(target_space["id"], c.user["couple_id"], a)
    await state.bump_taste_streak(c.uid, reset=True)
    return {"event": _brief(s), "invalid": errors, "widget": {"kind": "refresh"}}"""

    assert old_update_fn in c, "old_update_fn not found in tools.py"
    c = c.replace(old_update_fn, new_update_fn)

    # 3. Update qloo_recommend docstring
    old_qloo_rec = '''@tool("qloo_recommend", "qloo", """Ad-hoc taste-based recommendations from QLOO, blended for the couple (or one partner).
Use for quick questions like 'where should we eat in Goa tonight?' or 'songs for our first dance'. Shows cards in chat.
For full event plans use build_plan instead.""",'''

    new_qloo_rec = '''@tool("qloo_recommend", "qloo", """Ad-hoc taste-based recommendations from QLOO, blended for the couple (or one partner).
IMPORTANT RULES:
- For wedding/trip destinations (e.g. European destination, honeymoon, wedding city): use category="travel" (urn:entity:destination). NEVER use 'place' for destinations!
- For venues, restaurants, cafes in a specific city: use category="place" with location.
- For music/songs: use category="music".
Shows cards in chat. For full event plans use build_plan instead.""",'''

    assert old_qloo_rec in c, "old_qloo_rec not found in tools.py"
    c = c.replace(old_qloo_rec, new_qloo_rec)

    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("Patched tools.py successfully.")

def patch_state():
    path = "backend/app/services/state.py"
    with open(path, "r", encoding="utf-8") as f:
        c = f.read().replace("\r\n", "\n")

    old_director = """def director(s: Snapshot) -> dict:
    \"\"\"Return the single best next move. Keep goals tiny and human.\"\"\"
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
        if not s.partner and pname:
            nxt.update(stage="ready_to_plan", goal=f"Event details and {first}'s tastes are ready. But notice {pname} hasn't joined or shared tastes yet. "
                       f"Tell {first} warmly: 'We have your tastes and event details ready, but {pname} hasn't shared her aesthetic yet! "
                       f"WeaveWed is built to unite both your worlds into one masterplan. Shall we send {pname} an invite link first? "
                       f"(Or if you'd like a preliminary solo preview right now, just say the word and I'll weave it!)' "
                       "If they agree to invite, call invite_partner. Only call build_plan if they explicitly request a solo preview or insist on weaving it right now.",
                       detail={"uncovered": uncovered, "partner_pending": True})
        else:
            nxt.update(stage="ready_to_plan", goal=f"You know enough to start. Offer to weave their {sp_['title']} plan now; when they "
                       "agree call build_plan (it runs in the background — keep chatting while it builds).",
                       detail={"uncovered": uncovered})
        return nxt"""

    new_director = """def director(s: Snapshot) -> dict:
    \"\"\"Return the single best next move. Keep goals tiny, human, and strictly sequenced.\"\"\"
    prof = s.user.get("profile") or {}
    conv = s.conv or {}
    turns = conv.get("turn_count", 0)
    cov = coverage(s.my_facts)
    first = (s.user.get("name") or "").split(" ")[0] or "there"
    pname = (s.partner or {}).get("name") or prof.get("partner_name")
    avoid = ["asking more than ONE question in a message",
             "giving open-ended recommendations or destination lists before event basics & tastes are set",
             "listing many options in speech — show a widget instead",
             "repeating a question the user already answered (check TASTES, CULTURAL ROOTS and PROFILE first)"]
    nxt: dict = {"stage": "", "goal": "", "detail": {}, "avoid": avoid}

    # 1. Partner Onboarding (Bride joining Groom's existing space)
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
        return nxt

    # 2. Initial Welcome for solo user
    if turns < 2 and not prof.get("greeted"):
        nxt.update(stage="welcome", goal=f"Warmly welcome {first}. Introduce yourself in one line and ask, lightly, what "
                   "they're celebrating or planning right now. Do NOT ask for dates, budget or tastes yet.")
        return nxt

    # 3. Rapport (ask partner's name)
    if not pname and turns < 12:
        nxt.update(stage="rapport", goal="Get to know them a little: casually ask their partner's name (then later, how they "
                   "met) and save it with remember_about_us. Keep it playful; if they want to jump into planning, let them.",
                   detail={"missing_profile": ["partner_name"]})
        if s.space is None:
            nxt["goal"] += " If they already said what they're planning, create the event space first."
        return nxt

    # 4. Guide mode (create event space)
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

    # 5. Cultural Roots collection (Mandatory foundation for QLOO Cultural IQ)
    if not prof.get("heritage") and not prof.get("tradition") and turns < 15:
        nxt.update(stage="cultural_roots", goal=f"Ask {first} about your cultural roots & wedding traditions "
                   f"(e.g., Maharashtrian, Bengali, Punjabi, Gujarati, South Indian, Hindu, Sikh, inter-faith, etc.) "
                   f"so QLOO Cultural IQ can weave authentic rituals, traditional attire and regional cuisine into your {sp_['title']}. "
                   f"Save the answers immediately with save_cultural_roots.",
                   detail={"missing_profile": ["heritage", "tradition"]})
        return nxt

    focus = sp.TEMPLATES[sp_["type"]]["taste_focus"]
    uncovered = [c for c in focus if cov.get(c, 0) < 2]
    streak = conv.get("taste_streak", 0)

    # 6. Event basics (city, dates, budget)
    if sp_["missing_fields"]:
        f = sp_["missing_fields"][0]
        meta = sp.FIELD_META[f]
        nxt.update(stage="event_basics", goal=f"Ask ONLY for the {meta['label'].lower()} of their {sp_['title']} "
                   f"(field '{f}') in a natural way, then save it with update_event. If several details are still missing "
                   "and they're typing (not talking), you may instead offer the details form (ask_event_details).",
                   detail={"field": f, "remaining": sp_["missing_fields"]})
        return nxt

    # 7. Core tastes collection
    if uncovered and streak < 2 and not (sp_.get("active_plan_version")):
        c = uncovered[0]
        nxt.update(stage="know_tastes", goal=f"Get to know {first}'s taste in {CATEGORIES[c]['label']} — this matters for "
                   f"their {sp_['title']}. Ask it like a friend would, and call show_taste_picker(category='{c}'). One category only.",
                   detail={"category": c, "uncovered": uncovered, "coverage": cov})
        return nxt

    # 8. Partner Gatekeeper & Invitation
    if not s.partner and not prof.get("invite_offered"):
        nxt.update(stage="invite_partner", goal=f"Gently suggest inviting {pname or 'their partner'} so the plan is woven from "
                   "both tastes (call invite_partner if they agree). Mention it once only; don't block planning on it.")
        return nxt

    # 9. Ready to Plan (Enforce Dual Partner Gatekeeper)
    if not sp_.get("active_plan_version"):
        if not s.partner and pname:
            nxt.update(stage="ready_to_plan", goal=f"Event details and {first}'s tastes are ready. But notice {pname} hasn't joined or shared tastes yet. "
                       f"Tell {first} warmly: 'We have your tastes and event details ready, but {pname} hasn't shared her aesthetic yet! "
                       f"WeaveWed is built to unite both your worlds into one masterplan. Shall we send {pname} an invite link first? "
                       f"(Or if you'd like a preliminary solo preview right now, just say the word and I'll weave it!)' "
                       "If they agree to invite, call invite_partner. Only call build_plan if they explicitly request a solo preview or insist on weaving it right now.",
                       detail={"uncovered": uncovered, "partner_pending": True})
        elif s.partner and len(s.partner_facts) < 2:
            nxt.update(stage="ready_to_plan", goal=f"Event details and {first}'s tastes are set, but {pname} has only shared minimal tastes. "
                       f"Prompt: 'We're almost ready to weave the masterplan! Would {pname} like to add a couple more favorite artists or styles "
                       f"so the recommendations are 50/50 balanced? Or shall I weave what we have right now?' "
                       f"If they say go ahead, call build_plan.",
                       detail={"partner_facts_count": len(s.partner_facts)})
        else:
            nxt.update(stage="ready_to_plan", goal=f"Both partners' tastes and event foundations are locked in! Offer to weave their {sp_['title']} "
                       "plan now; when they agree call build_plan (it runs in the background — keep chatting while it builds).",
                       detail={"uncovered": uncovered})
        return nxt"""

    assert old_director in c, "old_director not found in state.py"
    c = c.replace(old_director, new_director)
    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("Patched state.py successfully.")

def patch_orchestrator():
    path = "backend/app/agent/orchestrator.py"
    with open(path, "r", encoding="utf-8") as f:
        c = f.read().replace("\r\n", "\n")

    # Wrap tool execution in try/except so tool error does not abort SSE stream
    old_call = 'result = await tc.call(fc.name, dict(fc.args or {}))'
    new_call = '''try:
                        result = await tc.call(fc.name, dict(fc.args or {}))
                    except Exception as tool_err:
                        log.warning("Tool %s execution error: %s", fc.name, tool_err)
                        result = {"error": f"Tool error: {tool_err}"}'''
    assert old_call in c, "old_call not found in orchestrator.py"
    c = c.replace(old_call, new_call)

    # Increase retry sleep for 429
    old_retry = 'await asyncio.sleep(0.6 * (attempt + 1))'
    new_retry = 'await asyncio.sleep(1.2 * (2 ** attempt))'
    if old_retry in c:
        c = c.replace(old_retry, new_retry)

    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("Patched orchestrator.py successfully.")

def patch_login():
    path = "frontend/src/pages/Login.tsx"
    with open(path, "r", encoding="utf-8") as f:
        c = f.read().replace("\r\n", "\n")

    old_up = """        if (app) {
          const c = await createUserWithEmailAndPassword(auth, email, pw);
          if (name) { await updateProfile(c.user, { displayName: name }); await c.user.getIdToken(true); }
        } else {
          const uid = email.split("@")[0].toLowerCase().replace(/[^a-z0-9]/g, "");
          localStorage.setItem("ww_dev_token", `dev-${uid}`);
          window.location.href = "/app";
        }"""

    new_up = """        if (app) {
          const c = await createUserWithEmailAndPassword(auth, email, pw);
          if (name) {
            try { await updateProfile(c.user, { displayName: name }); } catch {}
            try { await api("/api/me", { method: "PATCH", body: { name: name.trim() } }); } catch {}
            await c.user.getIdToken(true);
          }
        } else {
          const uid = email.split("@")[0].toLowerCase().replace(/[^a-z0-9]/g, "");
          localStorage.setItem("ww_dev_token", `dev-${uid}`);
          if (name) {
            try { await api("/api/me", { method: "PATCH", body: { name: name.trim() } }); } catch {}
          }
          window.location.href = "/app";
        }"""

    assert old_up in c, "old_up not found in Login.tsx"
    c = c.replace(old_up, new_up)
    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("Patched Login.tsx successfully.")

def patch_playbook():
    path = "backend/app/agent/prompts/tools_playbook.md"
    with open(path, "r", encoding="utf-8") as f:
        c = f.read().replace("\r\n", "\n")

    rules_addition = """
# CRITICAL WEAVEWED AGENTIC PROTOCOL & FOUNDATIONS (Follow strictly)
1. **Never Give Premature Recommendations or Destination Dumps**:
   - If the user asks "suggest something", "where should we go", or "plan my wedding" before basics & tastes exist:
     DO NOT dump random ideas or call qloo_recommend. Explain warmly:
     "I'd love to curate the perfect celebration for you! To make sure every venue, mood, and detail is tailored to your real aesthetic and budget via taste intelligence, let's first lock in your budget and wedding vibe."
2. **Handling Broad Concepts ("European destination", "foreign wedding")**:
   - QLOO is an Entity-to-Entity Correlation Graph. Broad phrases ("European destination", "foreign wedding") do NOT exist as entities in QLOO and will fail or return irrelevant items.
   - When a user expresses a broad concept, guide them to concrete entities:
     "A European destination wedding sounds breathtaking! To shape the plan, are you imagining the romantic coastal villas of Italy's Amalfi Coast, the fairytale châteaux of France, or the alpine lakes of Switzerland?"
   - Once they name a specific place (Amalfi, Paris, Lake Como, Interlaken), save it as the destination!
3. **Destinations vs Venues**:
   - For wedding/honeymoon destinations (cities, islands, countries), use `qloo_recommend(category="travel")`. NEVER use `place` for destinations! `place` is ONLY for specific venues/restaurants in a city.
4. **Cultural Roots are Mandatory**:
   - Before weaving the masterplan, ensure the couple's cultural heritage and wedding traditions are recorded using `save_cultural_roots`.
5. **Partner Gatekeeper**:
   - When the bride/partner joins, your #1 mission is to capture her unique aesthetic and cultural traditions so the plan is 50/50 balanced.
"""
    c = c.strip() + "\n" + rules_addition.strip() + "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("Patched tools_playbook.md successfully.")

if __name__ == "__main__":
    patch_auth()
    patch_spaces()
    patch_tools()
    patch_state()
    patch_orchestrator()
    patch_login()
    patch_playbook()
    print("ALL FIXES APPLIED SUCCESSFULLY!")

