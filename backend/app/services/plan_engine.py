"""Plan engine: QLOO candidates -> planner LLM (candidate-only) -> validated, progressive sections."""
import asyncio
import logging
import urllib.parse

from ..config import settings
from ..core.llm import gen_json
from ..db import db, get_doc, new_id, now_iso
from . import events, qloo
from .couple import decisions
from .memory import recall
from .notify import notify_many
from .spaces import TEMPLATES, seed_todos
from .tastes import disliked_ids, facts, signals

log = logging.getLogger("plan")
_locks: dict[str, asyncio.Lock] = {}
_tasks: set[asyncio.Task] = set()
_pending: set[str] = set()

_sem = asyncio.Semaphore(2)

ITEM_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "summary": {"type": "STRING"},
        "items": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
            "candidate_id": {"type": "STRING"},
            "title": {"type": "STRING"},
            "description": {"type": "STRING"},
            "why": {"type": "ARRAY", "items": {"type": "STRING"}},
            "est_cost": {"type": "NUMBER"},
            # Structured intelligence & deliverable attributes
            "track_title": {"type": "STRING"},
            "artist_name": {"type": "STRING"},
            "act": {"type": "STRING"},
            "tempo_bpm": {"type": "STRING"},
            "vibe_tag": {"type": "STRING"},
            "cue_note": {"type": "STRING"},
            "course_type": {"type": "STRING"},
            "heritage_origin": {"type": "STRING"},
            "portion_math": {"type": "STRING"},
            "bride_groom_pairing": {"type": "STRING"},
            "hex_colors": {"type": "ARRAY", "items": {"type": "STRING"}},
            "anti_clash_check": {"type": "STRING"},
            "capacity_check": {"type": "STRING"},
            "budget_breakdown": {"type": "STRING"},
            "lighting_spec": {"type": "STRING"},
        }, "required": ["title", "description", "why"]}},
    },
    "required": ["summary", "items"],
}


def _fact_lines(items: list[dict]) -> list[str]:
    out = []
    for f in sorted(items, key=lambda x: -x.get("confidence", 0))[:35]:
        s = f.get("sentiment", 0)
        mood = "LOVES" if s > 0.6 else ("likes" if s > 0 else "DISLIKES")
        priv = " (private: may influence choices, NEVER mention)" if f.get("visibility") == "private" else ""
        out.append(f"- {mood} [{f['category']}] {f['text']}{priv}")
    return out


async def _context(space: dict) -> dict:
    couple = await get_doc(f"couples/{space['couple_id']}")
    members = couple.get("members", [])
    users = await asyncio.gather(*[get_doc(f"users/{u}") for u in members])
    fs = await asyncio.gather(*[facts(u) for u in members])
    people = [{"uid": u, "name": (usr or {}).get("name", "Partner"), "facts": [f for f in f_ if f.get("source") != "hint"],
               "profile": (usr or {}).get("profile", {})} for u, usr, f_ in zip(members, users, fs)]
    eps, decs = await asyncio.gather(
        recall(space["couple_id"], f"{space['type']} {space.get('city', '')} {space.get('destination', '')}", 3),
        decisions(space["couple_id"], 12))
    decs = [d["summary"] for d in decs if not d.get("private_to")]
    return {"couple": couple, "people": people, "episodes": eps, "decisions": decs}


def _brief(space: dict, ctx: dict) -> str:
    keys = ["type", "title", "city", "start_date", "end_date", "budget", "currency", "guests", "ceremonies",
            "destination", "from_city", "travel_style", "mood", "occasion", "priorities"]
    lines = ["EVENT: " + ", ".join(f"{k}={space[k]}" for k in keys if space.get(k) not in (None, "", []))]
    for p in ctx["people"]:
        lines.append(f"PARTNER {p['name']}:")
        prof = p.get("profile") or {}
        cult = [f"{k}: {v}" for k, v in prof.items() if k in ("heritage", "tradition", "religion", "state", "country") and v]
        if cult:
            lines.append(f"  Cultural roots: {', '.join(cult)}")
        lines += _fact_lines(p["facts"]) or ["- (no tastes shared yet)"]
    dna = (ctx["couple"] or {}).get("dna") or {}
    if dna.get("cultural_harmony"):
        lines.append(f"CULTURAL HARMONY: {dna['cultural_harmony'].get('title')} — {dna['cultural_harmony'].get('summary')}")
        if dna['cultural_harmony'].get('ideas'):
            for idea in dna['cultural_harmony']['ideas']:
                lines.append(f"  * {idea.get('category', 'Fusion')}: {idea.get('title')} — {idea.get('description')}")
    if dna.get("vibe"):
        lines.append(f"COUPLE VIBE: {dna['vibe']} — {dna.get('description', '')}")
    if dna.get("shared"):
        lines.append("SHARED LOVES: " + ", ".join(s["name"] for s in dna["shared"][:15]))
    if ctx["decisions"]:
        lines.append("CONFIRMED DECISIONS (respect these): " + " | ".join(ctx["decisions"]))
    if ctx["episodes"]:
        lines.append("PAST EXPERIENCES (learn from these): " + " | ".join(
            f"{e.get('summary', '')} (loved: {e.get('highlights')}, disliked: {e.get('lowlights')})" for e in ctx["episodes"]))
    return "\n".join(lines)


async def _build_section(spec: dict, space: dict, ctx: dict, location: str | None, instruction: str | None,
                         prev: dict | None) -> dict:
    sec = {"key": spec["key"], "title": spec["title"], "kind": spec["kind"], "items": [], "summary": "",
           "error": None, "status": "done", "generated_at": now_iso()}
    candidates: list[dict] = []
    if spec["kind"] == "qloo":
        if spec["loc"] and not location:
            sec["error"] = "Add a city/destination to get these recommendations."
            return sec
        partner_sig = {p["uid"]: signals(p["facts"]) for p in ctx["people"]}
        exclude = set(space.get("excluded_ids") or [])
        for p in ctx["people"]:
            exclude |= disliked_ids(p["facts"])
        try:
            candidates = await qloo.blend(spec["qtype"], partner_sig, location, spec["take"], exclude)
        except Exception as e:
            try:
                log.info("qloo.blend retry for %s...", spec["key"])
                await asyncio.sleep(1.0)
                candidates = await qloo.blend(spec["qtype"], partner_sig, location, spec["take"], exclude)
            except Exception as e2:
                sec["error"] = "Taste intelligence is unavailable right now. Try refreshing this section in a minute."
                log.warning("blend failed %s: %s", spec["key"], e2)
                return sec
        if not candidates:
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
            candidates.sort(key=_venue_rank, reverse=True)
    cand_lines = [
        f"{c['entity_id']} | {c['name']} | tags: {', '.join(c.get('tags') or [])} | affinity: {round(c.get('affinity') or 0, 2)}"
        f"{' | LOVED BY BOTH' if c.get('loved_by_both') else ''} | {c.get('description', '')[:120]}"
        for c in candidates[:30]]
    other = ""
    if spec["key"] == "itinerary" and ctx.get("plan_so_far"):
        other = "RECOMMENDED PLACES ALREADY IN THIS PLAN (use these by name): " + "; ".join(ctx["plan_so_far"]) + "\n\n"
    # Dynamic metrics scaled to space budget and guest count
    guests = int(space.get("guests") or 250)
    budget = float(space.get("budget") or 2500000)
    venue_envelope = round(budget * 0.32)
    fb_envelope = round(budget * 0.25)
    decor_envelope = round(budget * 0.12)
    outfit_envelope = round(budget * 0.15)
    music_envelope = round(budget * 0.08)

    per_plate_target = round(fb_envelope / max(1, guests))
    anti_waste_standard_kg = round(guests * 0.38)
    anti_waste_buffer_kg = round(anti_waste_standard_kg * 0.12)
    ceremonies = space.get("ceremonies") or ["Haldi", "Mehendi", "Sangeet", "Wedding", "Reception"]

    special_rules = ""
    if spec["key"] in ("sangeet", "music"):
        cand_sample = ", ".join(c["name"] for c in candidates[:8]) if candidates else "blended artists"
        special_rules = f"""\n\nCRITICAL REQUIREMENTS FOR SANGEET & CEREMONY MUSIC BLUEPRINT:
1. Ground every single track strictly in the QLOO artist candidates above (e.g. {cand_sample}).
2. Structure the items following the Multi-Generational Sangeet Energy Curve across 5-6 items:
   - 'Act 1: Golden Hour Acoustic Sunset Bridge' (~75-85 BPM gentle romantic acoustic)
   - 'Act 2: Elders & Parents Flashmob' (~105-115 BPM retro/vintage crowd-pleasing melodious groove)
   - 'Act 3: Couple First Dance Medley' (~75-80 BPM intimate acoustic romance)
   - 'Act 4: High-Energy Youth & Sibling Dance Floor' (~125-135 BPM peak floor-filler Bollywood/Punjabi beat)
   - 'Act 5: Sacred Pheras & Bridal Entry Ambient' (Royal Shehnai / Sufi sacred ambient)
3. For EACH item, you MUST populate:
   - title: Specific Song/Track Title (e.g. 'Tum Ho', 'O Sanam', 'Kasoor', 'Kesariya', 'Subhanallah', 'Gud Naal Ishq Mitha', etc.)
   - candidate_id: The exact entity_id of the QLOO artist
   - artist_name: The QLOO artist's name
   - act: Exact act name (e.g. 'Act 1: Golden Hour Acoustic Sunset Bridge')
   - tempo_bpm: Specific tempo (e.g. '78 BPM - Gentle Sway', '128 BPM - Peak Floor-Filler')
   - vibe_tag: Short badge (e.g. 'Acoustic Soul', 'Retro Melodic', 'First Dance Medley', 'Peak Bolly Explosion', 'Sacred Royal')
   - cue_note: DJ / choreography cue note (e.g. 'Low-fog entry with acoustic guitar solo, transitioning to live dhol at chorus')
   - why: 2-3 specific reasons citing both partners' music tastes by name.\n"""
    elif spec["key"] == "menu":
        special_rules = f"""\n\nCRITICAL REQUIREMENTS FOR DUAL-HERITAGE ANTI-WASTE CATERING:
Dynamic Event Metrics:
- Guest Count: {guests} guests
- Total Wedding Budget: ₹{budget:,.0f} | F&B Catering Budget: ₹{fb_envelope:,.0f} (~₹{per_plate_target:,.0f}/plate target)
- Anti-Waste Baseline: {anti_waste_standard_kg} kg total food weight ({guests} guests x 380g standard portion)
- Waste Mitigation: -12% carb buffer (saving ~{anti_waste_buffer_kg} kg buffet binning) + staggered 30-min live batch replenishment

Design 5-6 structured catering courses/stations balancing both partners' cultural roots and dietary preferences:
1. Partner 1 Regional Heritage Live Counter (e.g., Live Mumbai/Pune Wada Pav fondue & chaat)
2. Partner 2 Regional Heritage Live Counter (e.g., Purani Dilli Kebab skewers / Kolkata Puchka shot bar)
3. Multi-Generational Main Feast Progression (mild elder-digestible gravies + rich festive curry)
4. WeaveWed Couple Special Fusion Dish (marrying both partners' favorite regional flavors)
5. Anti-Waste Starch & Bread Station (-12% calculated buffer with live tandoor roti/naan)
6. Artisanal Regional Dessert Counter (e.g. Shrikhand Tartlets & Nolen Gur Rosogolla)

For EACH item, you MUST populate:
- title: Station/Course Name
- course_type: 'Live Hometown Counter' | 'Main Feast' | 'Elder & Kids Friendly' | 'Couple Special' | 'Artisanal Dessert'
- heritage_origin: Name the cultural roots (e.g. 'Maharashtrian Roots', 'Awadhi / North Indian', 'Cross-Cultural Fusion')
- portion_math: Detailed anti-waste portion formula scaled for {guests} guests (e.g. 'Scaled for {guests} guests: 380g/plate sizing, 30-min live batch prep saves ~{anti_waste_buffer_kg}kg food waste')
- est_cost: Estimated station cost in INR within the ₹{fb_envelope:,.0f} catering envelope
- why: Reasons tied to both partners' food preferences and cultural background by name.\n"""
    elif spec["key"] == "outfits":
        special_rules = f"""\n\nCRITICAL REQUIREMENTS FOR CEREMONY OUTFITS & COLOR HARMONY:
Choose designer brands strictly from the QLOO brand candidates above.
For each wedding ceremony ({', '.join(ceremonies[:5])}), provide 4-5 ceremony outfits with exact color pairings and zero-backdrop clash check:
For EACH item, you MUST populate:
- title: Ceremony Name & Aesthetic Look (e.g. 'Haldi Morning: Sunflower & Raw Ivory Sunburst', 'Sangeet Night: Midnight Indigo & Champagne Glamour', 'Sacred Pheras: Royal Vermillion & Antique Gold')
- candidate_id: The QLOO designer brand's entity_id
- bride_groom_pairing: Specific pairing (e.g. 'Bride: Mustard Yellow Raw Silk Lehenga with Gota Patti | Groom: Ivory Chanderi Silk Kurta with Mustard Bandi')
- hex_colors: Array of 2-3 exact HEX color codes (e.g. ['#E1AD01', '#FFFFF0', '#D4AF37'])
- anti_clash_check: Zero-backdrop clash statement (e.g. '100% clash-free verified: High contrast against green foliage & marigold mandap backdrop')
- description: Fabrics (Chanderi, Raw Silk, Organza, Velvet), silhouettes, and lighting suitability.
- why: 2-3 specific reasons tied to partners' fashion tastes and heritage.\n"""
    elif spec["key"] in ("ceremonies", "decor"):
        special_rules = f"""\n\nCRITICAL REQUIREMENTS FOR STAGE & MANDAP DECORATION THEMES:
Provide 4-5 architectural decor concepts for the wedding ceremonies within the ₹{decor_envelope:,.0f} decor envelope:
For EACH item, you MUST populate:
- title: Ceremony & Theme (e.g. 'Sacred Mandap: 4-Pillar Open Rajwada Stone Canopy', 'Sangeet Stage: Geometric Jali & 2700K Warm Brass Screen')
- hex_colors: Array of 3 exact HEX color codes for floral & backdrop palette (e.g. ['#FFA500', '#F8F8FF', '#B5A642'])
- lighting_spec: Ambient lighting temperature and camera spec (e.g. '2700K warm incandescent glow with diffused key lights, zero fluorescent glare for 4K video')
- description: Architectural structure, floral varieties, and photo backdrop contrast for phone & DSLR cameras.
- why: Tied to couple vibe, aesthetic DNA, and romantic atmosphere.\n"""
    elif spec["key"] == "venue":
        special_rules = f"""\n\nCRITICAL REQUIREMENTS FOR VENUE SHORTLIST:
Dynamic Event Metrics:
- Guest Count: {guests} guests
- Total Wedding Budget: ₹{budget:,.0f} | Venue Envelope (32%): ₹{venue_envelope:,.0f}
Choose ONLY from the QLOO venue candidates above.
For EACH item, you MUST populate:
- title: Venue name
- candidate_id: The QLOO venue candidate's entity_id
- capacity_check: State capacity buffer for {guests} guests (e.g. 'Capacity: 450 guests (Comfortably accommodates your {guests} guests with ~25% buffer)')
- budget_breakdown: Estimated rental vs per-plate cost (e.g. 'Est. Rental: ₹3.5L | F&B Target: ₹1,800/plate within your ₹{venue_envelope:,.0f} venue envelope')
- why: Specific reasons tied to atmosphere, hospitality, and couple vibe.\n"""
    prompt = (
        f"You are WeaveWed, a warm and expert Indian wedding & couple planner. Write the plan section '{spec['title']}'.\n"
        f"Section brief: {spec['brief']}\n\n{_brief(space, ctx)}\n\n{other}"
        + (f"USER CHANGE REQUEST (highest priority): {instruction}\n\n" if instruction else "")
        + (f"PREVIOUS VERSION OF THIS SECTION: {[i['title'] for i in prev.get('items', [])]}\n\n" if prev and instruction else "")
        + ("CANDIDATES from QLOO taste intelligence (choose ONLY from these; copy the id into candidate_id exactly):\n"
           + "\n".join(cand_lines) if candidates else "This is an ideas section: write original, specific ideas (candidate_id empty).")
        + special_rules
        + "\n\nRules: choose 4-6 items that genuinely fit THIS event and brief (skip candidates that don't fit, e.g. a "
          "museum in a food section, a hotel in a music section). Each 'why' = 2-3 short, specific reasons tied to the "
          "partners' tastes BY NAME (never mention private tastes). est_cost = rough INR estimate or 0 if unknown. "
          "Respect dislikes and confirmed decisions. summary = one warm sentence to the couple."
    )
    out = None
    for attempt in range(3):
        try:
            async with _sem:
                out = await gen_json(prompt, ITEM_SCHEMA, model=settings.GEMINI_PLANNER_MODEL, temperature=0.5, thinking=None)
            break
        except Exception as e:
            if attempt < 2 and ("429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)):
                log.info("Rate limited generating %s, retrying in %ds...", spec["key"], 2 * (attempt + 1))
                await asyncio.sleep(2 * (attempt + 1))
                continue
            log.warning("planner failed %s: %s", spec["key"], e)
            sec["error"] = "The planner hit a snag on this section. Refresh to try again."
            return sec
    by_id = {c["entity_id"]: c for c in candidates}
    by_name = {c["name"].lower(): c for c in candidates}
    prev_status = {(it.get("entity_id") or it["title"].lower()): it.get("status", "suggested") for it in (prev or {}).get("items", [])}
    where = location or space.get("city") or ""
    for it in out.get("items", [])[:6]:
        c = by_id.get((it.get("candidate_id") or "").strip()) or by_name.get((it.get("title") or "").strip().lower())
        if spec["kind"] == "qloo" and not c:
            art_nm = (it.get("artist_name") or "").strip().lower()
            if art_nm and art_nm in by_name:
                c = by_name[art_nm]
            else:
                for cand in candidates:
                    c_low = cand["name"].lower()
                    if c_low in it.get("title", "").lower() or c_low in it.get("artist_name", "").lower() or c_low in it.get("description", "").lower():
                        c = cand
                        break
        if spec["kind"] == "qloo" and not c and spec["key"] not in ("sangeet", "music"):
            continue  # guardrail: never invent recommendations

        if spec["key"] in ("sangeet", "music"):
            track = it.get("track_title") or it.get("title")
            art = (c["name"] if c else it.get("artist_name")) or ""
            title = f"{track} — {art}" if art and art.lower() not in track.lower() else track
        else:
            title = c["name"] if c and spec["key"] in ("venue", "outfits") else it["title"]

        item = {"id": new_id("i"), "title": title, "description": it.get("description", ""), "why": it.get("why", [])[:3],
                "est_cost": max(0, it.get("est_cost") or 0), "entity_id": c["entity_id"] if c else None,
                "image": c.get("image") if c else None, "affinity": c.get("affinity") if c else None,
                "loved_by_both": bool(c and c.get("loved_by_both")), "tags": c.get("tags", []) if c else [],
                "address": c.get("address") if c else None,
                "status": prev_status.get((c["entity_id"] if c else title.lower()), "suggested")}

        for field in ("track_title", "artist_name", "act", "tempo_bpm", "vibe_tag", "cue_note",
                      "course_type", "heritage_origin", "portion_math", "bride_groom_pairing",
                      "hex_colors", "anti_clash_check", "capacity_check", "budget_breakdown", "lighting_spec"):
            if it.get(field):
                item[field] = it[field]
        if c and not item.get("artist_name") and spec["key"] in ("sangeet", "music"):
            item["artist_name"] = c["name"]

        if c and spec["qtype"] in (qloo.PLACE, qloo.DEST):
            q = f"{title} {where}" if spec["qtype"] == qloo.PLACE else title
            item["maps_url"] = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(q.strip())
        sec["items"].append(item)
    sec["summary"] = out.get("summary", "")
    if not sec["items"]:
        sec["error"] = "Couldn't find great matches this time. Share a few more tastes and refresh."
    return sec


def _budget(space: dict, overrides: list | None = None) -> list[dict]:
    total = float(space.get("budget") or 0)
    split = overrides or [{"category": k, "pct": v} for k, v in TEMPLATES[space["type"]]["budget"].items()]
    s = sum(max(0.0, float(x["pct"])) for x in split) or 100
    return [{"category": x["category"], "pct": round(100 * max(0.0, float(x["pct"])) / s, 1),
             "amount": round(total * max(0.0, float(x["pct"])) / s)} for x in split]


async def latest_plan(space: dict, include_building: bool = False) -> dict | None:
    v = (space.get("building_version") if include_building else None) or space.get("active_plan_version") or 0
    return await get_doc(f"spaces/{space['id']}/plans/v{v}") if v else None


def is_building(space_id: str) -> bool:
    return space_id in _pending or (_locks.get(space_id) is not None and _locks[space_id].locked())


async def start_build(space_id: str, section_keys: list[str] | None = None, instruction: str | None = None,
                      by_uid: str | None = None) -> bool:
    """Fire-and-forget. Marks the space 'building' immediately (UI starts polling at once).
    Returns False if a build is already running for this space."""
    lock = _locks.setdefault(space_id, asyncio.Lock())
    if lock.locked() or space_id in _pending:
        return False
    _pending.add(space_id)
    try:
        await db.document(f"spaces/{space_id}").update({"state": "building", "build_error": None, "building_started_at": now_iso()})
    except Exception:  # noqa
        _pending.discard(space_id)
        raise
    t = asyncio.create_task(_run_build(space_id, section_keys, instruction, by_uid))
    _tasks.add(t)
    t.add_done_callback(_tasks.discard)
    return True


async def _run_build(space_id, keys, instruction, by_uid):
    try:
        await build(space_id, keys, instruction, by_uid)
    except Exception:  # noqa
        log.exception("background build failed")
    finally:
        _pending.discard(space_id)


async def build(space_id: str, section_keys: list[str] | None = None, instruction: str | None = None,
                by_uid: str | None = None) -> dict:
    lock = _locks.setdefault(space_id, asyncio.Lock())
    async with lock:
        space = await get_doc(f"spaces/{space_id}")
        prev_state = space.get("prev_state") or ("planned" if space.get("active_plan_version") else "ready")
        ctx = await _context(space)
        members = ctx["couple"]["members"]
        prev = await latest_plan(space)
        prev_secs = {s["key"]: s for s in (prev or {}).get("sections", [])}
        specs = list(TEMPLATES[space["type"]]["sections"])
        if space["type"] in ("trip", "honeymoon") and space.get("destination"):
            specs = [s for s in specs if s["key"] != "destinations"]
        if space["type"] == "wedding" and not space.get("ceremonies"):
            specs = [s for s in specs if s["key"] != "ceremonies"]
        valid_keys = {s["key"] for s in specs}
        keys = [k for k in (section_keys or []) if k in valid_keys] or None
        todo = [s for s in specs if not keys or s["key"] in keys]
        version = (space.get("active_plan_version") or 0) + 1
        ref = db.document(f"spaces/{space_id}/plans/v{version}")
        results: dict[str, dict] = {}
        for s in specs:
            if s in todo:
                results[s["key"]] = {"key": s["key"], "title": s["title"], "kind": s["kind"], "items": [], "status": "pending"}
            elif s["key"] in prev_secs:
                results[s["key"]] = prev_secs[s["key"]]
        write_lock = asyncio.Lock()

        async def flush(status="building"):
            async with write_lock:
                await ref.set({"version": version, "status": status, "instruction": instruction,
                               "sections": [results[s["key"]] for s in specs if s["key"] in results],
                               "budget": _budget(space, (prev or {}).get("budget_overrides")),
                               "budget_overrides": (prev or {}).get("budget_overrides"),
                               "dna_version": ((ctx["couple"] or {}).get("dna") or {}).get("version", 0),
                               "destination_used": dest_used[0], "created_at": now_iso(), "by_uid": by_uid})

        dest_used = [space.get("destination")]
        await db.document(f"spaces/{space_id}").update({"state": "building", "building_version": version, "build_error": None})
        await flush()
        sem = asyncio.Semaphore(3)

        async def run(spec, loc):
            async with sem:
                results[spec["key"]] = await _build_section(spec, space, ctx, loc, instruction, prev_secs.get(spec["key"]))
                await flush()

        try:
            loc_city = space.get("city")
            phase1 = [s for s in todo if s["loc"] != "destination" and s["key"] != "itinerary"]
            await asyncio.gather(*[run(s, loc_city if s["loc"] == "city" else None) for s in phase1])
            if not dest_used[0]:
                d = results.get("destinations", {}).get("items") or prev_secs.get("destinations", {}).get("items") or []
                dest_used[0] = d[0]["title"] if d else None
            phase2 = [s for s in todo if s["loc"] == "destination"]
            await asyncio.gather(*[run(s, dest_used[0]) for s in phase2])
            ctx["plan_so_far"] = [i["title"] for k in ("experiences", "food_trail") for i in results.get(k, {}).get("items", [])]
            for s in [s for s in todo if s["key"] == "itinerary"]:
                await run(s, dest_used[0])
            await flush("done")
            await db.document(f"spaces/{space_id}").update(
                {"state": "planned", "active_plan_version": version, "building_version": None})
            await seed_todos(space_id, space)
            ready = [results[s["key"]] for s in specs if s["key"] in results]
            summary = {"sections": [{"key": s["key"], "title": s["title"], "top": [i["title"] for i in s.get("items", [])[:3]],
                                     "error": s.get("error")} for s in ready]}
            msg = (f"Your {space.get('title')} plan was updated" + (f" — {instruction}" if instruction else "") + " ✨"
                   if prev else f"Your {space.get('title')} plan is ready ✨")
            await notify_many(members, msg, f"/app/spaces/{space_id}", "plan")
            events.publish(members, {"type": "plan_ready", "space_id": space_id, "title": space.get("title"),
                                     "instruction": instruction, "summary": summary, "by_uid": by_uid})
            return {"version": version, **summary}
        except Exception as e:
            log.exception("plan build failed")
            await ref.update({"status": "failed"})
            await db.document(f"spaces/{space_id}").update(
                {"state": prev_state if prev_state not in (None, "building") else "ready", "building_version": None,
                 "build_error": str(e)[:300]})
            events.publish(members, {"type": "plan_failed", "space_id": space_id, "error": str(e)[:200]})
            raise


async def set_budget(space: dict, allocations: list[dict]) -> dict:
    plan = await latest_plan(space)
    if not plan:
        raise ValueError("Build the plan first")
    alloc = [{"category": str(a["category"])[:40], "pct": max(0.0, float(a["pct"]))} for a in allocations if a.get("category")]
    if not alloc or sum(a["pct"] for a in alloc) <= 0:
        raise ValueError("Give at least one category with a positive percentage")
    budget = _budget(space, alloc)
    await db.document(f"spaces/{space['id']}/plans/v{space['active_plan_version']}").update(
        {"budget": budget, "budget_overrides": alloc})
    return {"budget": budget}


def sections_for_categories(space_type: str, categories: set) -> list[str]:
    from .taste_intel import CATEGORIES
    types = {t for c in categories for t in CATEGORIES.get(c, {}).get("types", [])}
    keys = []
    for s in TEMPLATES[space_type]["sections"]:
        if s["kind"] == "idea" or s["qtype"] in types or (categories & {"food", "place"} and s["qtype"] == qloo.PLACE):
            keys.append(s["key"])
    return keys
