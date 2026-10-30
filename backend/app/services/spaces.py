"""Event Space templates, validation and CRUD."""
from datetime import date, timedelta

from fastapi import HTTPException

from ..core.timeutil import today, valid_date
from ..db import db, get_doc, list_col, new_id, now_iso
from . import qloo

PLACE, ARTIST, BRAND, DEST, MOVIE = qloo.PLACE, qloo.ARTIST, qloo.BRAND, qloo.DEST, qloo.MOVIE


def S(key, title, kind, brief, qtype=None, loc=None, take=25):
    return {"key": key, "title": title, "kind": kind, "brief": brief, "qtype": qtype, "loc": loc, "take": take}


CEREMONIES = ["Roka", "Haldi", "Mehendi", "Sangeet", "Wedding", "Reception", "Cocktail"]

FIELD_META = {
    "title": {"label": "Name this event", "kind": "text"},
    "city": {"label": "City", "kind": "text"},
    "start_date": {"label": "Date", "kind": "date"},
    "end_date": {"label": "End date", "kind": "date"},
    "budget": {"label": "Budget (₹)", "kind": "number"},
    "guests": {"label": "Guest count", "kind": "number"},
    "ceremonies": {"label": "Ceremonies", "kind": "multi", "options": CEREMONIES},
    "destination": {"label": "Destination (leave empty and I'll suggest)", "kind": "text"},
    "from_city": {"label": "Travelling from", "kind": "text"},
    "travel_style": {"label": "Travel style", "kind": "select",
                     "options": ["Relaxed", "Adventure", "Culture & heritage", "Luxury", "Nature", "Food & nightlife"]},
    "mood": {"label": "Mood", "kind": "select", "options": ["Romantic", "Fun & candid", "Royal", "Nature", "Vintage", "Modern"]},
    "occasion": {"label": "Occasion", "kind": "select",
                 "options": ["Anniversary", "Birthday", "Date night", "Baby shower", "House-warming", "Other"]},
    "priorities": {"label": "What matters most to you?", "kind": "text"},
}

TEMPLATES = {
    "prewedding": {
        "label": "Prewedding", "required": ["city", "start_date", "budget"], "optional": ["mood", "priorities"],
        "taste_focus": ["film", "music", "fashion", "place"],
        "sections": [
            S("shoot_locations", "Shoot Locations", "qloo", "Photogenic places in the city for a prewedding shoot (heritage, gardens, cafes, scenic spots) that fit the couple's vibe.", PLACE, "city", 40),
            S("theme", "Shoot Theme & Mood", "idea", "3-4 shoot concepts inspired by the couple's shared films, music and style, with outfit and prop ideas."),
            S("music", "Reel & Save-the-Date Music", "qloo", "Artists for reels and the save-the-date video.", ARTIST),
            S("outfits", "Outfit Mood", "qloo", "Fashion brands/designers whose style suits both partners for the shoot.", BRAND),
            S("dates", "Date & Proposal Experiences", "qloo", "Romantic restaurants, cafes and experiences in the city for dates or a proposal.", PLACE, "city", 40),
        ],
        "budget": {"Photographer & shoot": 40, "Outfits & styling": 30, "Experiences & dates": 20, "Misc": 10},
        "todos": [("Pick a shoot theme", -45), ("Book photographer", -40), ("Finalize outfits", -20), ("Confirm locations & permissions", -10)],
    },
    "engagement": {
        "label": "Engagement", "required": ["city", "start_date", "guests", "budget"], "optional": ["priorities"],
        "taste_focus": ["music", "food", "fashion"],
        "sections": [
            S("venue", "Venue Style & Shortlist", "qloo", "Hotels, banquets, gardens or restaurants in the city suitable for an engagement party of this size.", PLACE, "city", 40),
            S("menu", "Menu Direction", "idea", "Cuisines, signature dishes and a 'couple special' dish from both partners' food tastes."),
            S("music", "Music & Entertainment", "qloo", "Artists for the engagement playlist and entertainment style.", ARTIST),
            S("decor", "Decor Palette", "idea", "Decor theme, colour palette and 3-4 decor ideas matching the couple vibe."),
            S("outfits", "Outfit Coordination", "qloo", "Designers/brands for coordinated looks for both partners.", BRAND),
        ],
        "budget": {"Venue": 35, "Food & catering": 30, "Decor": 12, "Outfits & rings": 15, "Music": 5, "Misc": 3},
        "todos": [("Finalize venue", -60), ("Fix menu & caterer", -40), ("Outfit shopping", -30), ("Send invites", -25), ("Confirm decor & music", -7)],
    },
    "wedding": {
        "label": "Wedding", "required": ["city", "start_date", "guests", "budget", "ceremonies"], "optional": ["end_date", "priorities"],
        "taste_focus": ["music", "food", "fashion", "film"],
        "sections": [
            S("venue", "Venue Shortlist", "qloo", "Wedding venues — palaces, resorts, heritage hotels, banquets or lawns — in the city verified against guest capacity and 32% venue budget.", PLACE, "city", 40),
            S("ceremonies", "Stage & Mandap Decoration Themes", "idea", "Architectural mandap concepts, floral palettes with exact hex codes, and 2700K warm lighting for each ceremony."),
            S("sangeet", "Curated Song & Music Blueprint", "qloo", "Multi-generational Sangeet energy curve and tracklist with actual songs, tempo BPM, and choreography cues grounded in blended artists.", ARTIST, None, 30),
            S("menu", "Anti-Waste Dual-Tradition Catering", "idea", "Structured catering courses balancing both heritages with dynamic anti-waste portioning math scaled to guest count."),
            S("outfits", "Ceremony Outfits & Color Harmony", "qloo", "Designers, exact bride & groom color pairings with hex swatches, and zero-backdrop clash check.", BRAND),
            S("story_touches", "Couple Story Touches & Film Moments", "qloo", "Films the couple loves, used for cinematic entries, photo-ops, and personalized cocktail bars.", MOVIE, None, 15),
        ],
        "budget": {"Venue": 30, "Food & catering": 25, "Decor": 12, "Outfits & jewellery": 15, "Music & entertainment": 8, "Photo & video": 7, "Misc": 3},
        "todos": [("Shortlist & visit venues", -150), ("Book venue", -120), ("Book photographer", -100), ("Finalize caterer & menu", -90),
                  ("Designer outfit orders", -75), ("Send invitations", -45), ("Sangeet choreography & playlist", -30), ("Final vendor confirmations", -7)],
    },
    "honeymoon": {
        "label": "Honeymoon", "required": ["start_date", "end_date", "budget"], "optional": ["destination", "from_city", "travel_style"],
        "taste_focus": ["travel", "food", "experience", "music"],
        "sections": [
            S("destinations", "Destination Match", "qloo", "Honeymoon destinations ranked by how well they fit both partners.", DEST, None, 20),
            S("experiences", "Places & Experiences", "qloo", "Attractions, viewpoints, beaches, activities and romantic spots at the destination.", PLACE, "destination", 40),
            S("food_trail", "Food Trail", "qloo", "Restaurants, cafes and bars at the destination both would love.", PLACE, "destination", 40),
            S("itinerary", "Day-wise Itinerary", "idea", "A day-by-day plan for the exact trip dates balancing his, her and together moments, using the recommended places by name."),
            S("romantic", "Romantic Moments", "idea", "Sunset spots, special dinners and small surprise ideas for the trip."),
        ],
        "budget": {"Stay": 40, "Travel": 30, "Food": 15, "Experiences": 15},
        "todos": [("Book flights", -45), ("Book stays", -40), ("Visa / documents check", -30), ("Pre-book key experiences", -14), ("Pack", -2)],
    },
    "trip": {
        "label": "Trip", "required": ["start_date", "end_date", "budget"], "optional": ["destination", "from_city", "travel_style"],
        "taste_focus": ["travel", "food", "experience"],
        "sections": [
            S("destinations", "Where to Go", "qloo", "Destinations that fit both partners.", DEST, None, 20),
            S("experiences", "Places & Experiences", "qloo", "Attractions, activities and scenic spots at the destination.", PLACE, "destination", 40),
            S("food_trail", "Food Spots", "qloo", "Restaurants and cafes at the destination both would love.", PLACE, "destination", 40),
            S("itinerary", "Itinerary", "idea", "Day-wise plan for the exact dates using the recommended places by name, plus a rainy-day plan B."),
        ],
        "budget": {"Stay": 40, "Travel": 30, "Food": 15, "Experiences": 15},
        "todos": [("Book travel", -21), ("Book stay", -14), ("Shortlist must-dos", -5), ("Pack", -1)],
    },
    "life_beyond": {
        "label": "Life Beyond", "required": ["occasion", "start_date"], "optional": ["city", "budget"],
        "taste_focus": ["food", "experience", "music", "fashion"],
        "sections": [
            S("ideas", "Celebration Ideas", "idea", "4-5 celebration ideas for this occasion built from what both partners love and their shared history."),
            S("places", "Places to Celebrate", "qloo", "Restaurants and experiences in the city for this occasion.", PLACE, "city", 40),
            S("gifts", "Gift Ideas", "qloo", "Brands the partner(s) would love as gifts.", BRAND),
            S("music", "Mood Music", "qloo", "Artists for the celebration playlist.", ARTIST, None, 15),
        ],
        "budget": {"Experience": 50, "Gifts": 30, "Food": 20},
        "todos": [("Decide the plan", -10), ("Book place", -7), ("Get the gift", -3)],
    },
}
SPACE_FIELDS = set(FIELD_META)


def clean_fields(raw: dict, space_type: str | None = None) -> tuple[dict, list[str]]:
    """Validate & normalise. Returns (clean, errors) — errors go back to the agent/user verbatim."""
    out, errors = {}, []
    for k, v in (raw or {}).items():
        if k not in SPACE_FIELDS or v is None or v == "" or v == []:
            continue
        if k == "budget":
            try:
                v = float(str(v).replace(",", "").replace("₹", "").strip())
                if v <= 0:
                    raise ValueError
            except ValueError:
                errors.append("budget must be a positive number in rupees (e.g. 2500000 for 25 lakh)")
                continue
        elif k == "guests":
            try:
                v = int(float(str(v)))
                if v <= 0 or v > 20000:
                    raise ValueError
            except ValueError:
                errors.append("guests must be a positive whole number")
                continue
        elif k == "ceremonies":
            if isinstance(v, str):
                v = [x.strip() for x in v.split(",") if x.strip()]
            v = [str(x).strip().title()[:30] for x in v if str(x).strip()][:12]
        elif k in ("start_date", "end_date"):
            d = valid_date(v)
            if not d:
                errors.append(f"{k} must be a date in YYYY-MM-DD format")
                continue
            v = d
        else:
            v = str(v).strip()[:120]
        out[k] = v
    if out.get("start_date") and out.get("end_date") and out["end_date"] < out["start_date"]:
        errors.append("end_date can't be before start_date")
        out.pop("end_date")
    return out, errors


def missing_fields(space: dict) -> list[str]:
    return [f for f in TEMPLATES[space["type"]]["required"] if space.get(f) in (None, "", [])]


def field_specs(space_type: str, only: list[str] | None = None) -> list[dict]:
    t = TEMPLATES[space_type]
    keys = only or (t["required"] + t["optional"])
    return [{"key": k, **FIELD_META[k], "required": k in t["required"]} for k in keys]


def compute_state(space: dict) -> str:
    st = space.get("state")
    if st in ("building", "completed"):
        return st
    if missing_fields(space):
        return "draft"
    if space.get("active_plan_version"):
        return st if st in ("planned", "stale") else "planned"
    return "ready"


def public(space: dict) -> dict:
    s = {k: v for k, v in space.items() if k not in ("excluded_ids",)}
    s["missing_fields"] = missing_fields(space)
    return s


async def get_space(sid: str, couple_id: str) -> dict:
    s = await get_doc(f"spaces/{sid}")
    if not s or s.get("couple_id") != couple_id:
        raise HTTPException(404, "Event space not found")
    s["missing_fields"] = missing_fields(s)
    return s


async def list_spaces(couple_id: str) -> list[dict]:
    out = []
    async for snap in db.collection("spaces").where("couple_id", "==", couple_id).stream():
        d = snap.to_dict()
        d["id"] = snap.id
        out.append(public(d))
    out.sort(key=lambda s: s.get("created_at", ""), reverse=True)
    return out


async def check_schedule_conflict(couple_id: str, start_date: str, end_date: str | None = None, exclude_sid: str | None = None) -> dict | None:
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


async def create_space(user: dict, stype: str, fields: dict) -> tuple[dict, list[str]]:
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
    return public(space), errors


async def update_space(sid: str, couple_id: str, fields: dict) -> tuple[dict, list[str]]:
    space = await get_space(sid, couple_id)
    f, errors = clean_fields(fields, space["type"])
    if f.get("start_date") and not f.get("end_date") and space.get("end_date") and space["end_date"] < f["start_date"]:
        f["end_date"] = None
    if f.get("end_date") and not f.get("start_date") and space.get("start_date") and f["end_date"] < space["start_date"]:
        errors.append("end_date can't be before the start date")
        f.pop("end_date")
    key_changed = any(k in f and f[k] != space.get(k) for k in
                      ("city", "start_date", "end_date", "budget", "guests", "ceremonies", "destination"))
    space.update(f)
    st = compute_state(space)
    if st == "planned" and key_changed:
        st = "stale"
    f["state"] = st
    if f:
        await db.document(f"spaces/{sid}").update(f)
    space["state"] = st
    return public(space), errors


def todo_seeds(space: dict) -> list[dict]:
    try:
        d0 = date.fromisoformat(space.get("start_date", ""))
    except ValueError:
        d0 = None
    t0 = today()
    out = []
    for title, off in TEMPLATES[space["type"]]["todos"]:
        due = d0 + timedelta(days=off) if d0 else None
        if due and due < t0:
            due = t0
        out.append({"title": title, "due": due.isoformat() if due else None})
    return out


async def seed_todos(sid: str, space: dict):
    if await list_col(db.collection(f"spaces/{sid}/todos"), limit=1):
        return
    for t in todo_seeds(space):
        await db.document(f"spaces/{sid}/todos/{new_id('t')}").set(
            {**t, "done": False, "assignee": None, "source": "plan", "created_at": now_iso()})
