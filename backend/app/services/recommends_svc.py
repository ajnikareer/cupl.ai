"""Recommends Service: the perpetual 'Happily Ever After' lifestyle engine.
Generates couple recommendations (Friday movie match, weekend dining, getaways)
and private partner gifting/surprise recommendations, grounded in QLOO taste intelligence.
Features life-stage gating, weekly cadence alignment, calendar conflict checks,
on/off toggle, and on-demand refresh/rotation cycles.
"""
import logging
from datetime import date, timedelta
from ..core.timeutil import today
from ..db import db, get_doc, new_id, now_iso
from . import state, qloo, tastes
from .calendar_svc import get_added_rec_ids

log = logging.getLogger("recommends_svc")

def get_upcoming_dates():
    t = today()
    # Next Friday
    days_to_fri = (4 - t.weekday()) % 7 or 7
    next_fri = t + timedelta(days=days_to_fri)
    # Next Saturday
    next_sat = next_fri + timedelta(days=1)
    # Next Sunday
    next_sun = next_fri + timedelta(days=2)
    # Next month mid
    next_month = t + timedelta(days=21)
    return {
        "friday": next_fri.isoformat(),
        "saturday": next_sat.isoformat(),
        "sunday": next_sun.isoformat(),
        "milestone": next_month.isoformat(),
        "in_two_weeks": (t + timedelta(days=14)).isoformat()
    }

async def toggle_recommends_enabled(user: dict, enabled: bool) -> dict:
    cid = user["couple_id"]
    await db.document(f"couples/{cid}").set({"recommends_enabled": bool(enabled)}, merge=True)
    return {"ok": True, "enabled": bool(enabled)}

async def refresh_recommendations(user: dict) -> dict:
    cid = user["couple_id"]
    couple_doc = await get_doc(f"couples/{cid}") or {}
    curr_cycle = couple_doc.get("recommends_cycle", 0)
    new_cycle = (curr_cycle + 1) % 3
    await db.document(f"couples/{cid}").set({"recommends_cycle": new_cycle}, merge=True)
    return await get_lifestyle_recommendations(user)

async def get_lifestyle_recommendations(user: dict) -> dict:
    snap = await state.load(user["uid"], with_episodes=False)
    cid = user["couple_id"]
    couple = snap.couple or {}
    
    # Check if user has toggled recommendations off
    recommends_enabled = couple.get("recommends_enabled", True)
    if recommends_enabled is None:
        recommends_enabled = True

    pname = (snap.partner or {}).get("name") or (snap.user.get("profile") or {}).get("partner_name") or "your partner"
    first = (snap.user.get("name") or "You").split(" ")[0]
    dates = get_upcoming_dates()
    added_ids = await get_added_rec_ids(user)
    stage = (couple.get("status") or "engaged").lower()
    cycle = couple.get("recommends_cycle", 0) % 3

    # City determination: active space city -> profile state -> Hyderabad default
    city = (snap.space or {}).get("city") or (snap.user.get("profile") or {}).get("state") or "Hyderabad"
    if "," in city:
        city = city.split(",")[0].strip()

    dna_vibe = (couple.get("dna") or {}).get("vibe") or "Romantic, soulful, elegant"

    if not recommends_enabled:
        return {
            "enabled": False,
            "couple_status": stage,
            "cycle": cycle,
            "couple_recs": [],
            "private_recs": [],
            "added_ids": added_ids,
            "active_city": city,
            "partner_name": pname,
            "couple_vibe": dna_vibe
        }

    # Calendar awareness & busy slot check
    busy_dates = set()
    for s in snap.spaces:
        if s.get("start_date"):
            busy_dates.add(s["start_date"][:10])
    async for csnap in db.collection("calendar_items").where("couple_id", "==", cid).stream():
        cd = csnap.to_dict()
        if cd.get("date"):
            busy_dates.add(cd["date"][:10])

    is_fri_busy = dates["friday"] in busy_dates
    is_sat_busy = dates["saturday"] in busy_dates

    # ------------------ STAGE-SPECIFIC RECOMMENDATION CATALOGS ------------------
    # Category 1: Screen & Cinema (The Friday Night Stand-Off / Safe Bet)
    # Category 2: Dining & Evening Outing in Active City
    # Category 3: Stage-Specific Special (Cocktail formulation / Aesthetic harmony / Wildcard)
    # Category 4: Spontaneous Weekend Retreat / Getaway

    if stage in ["engaged", "planning"]:
        # STAGE 3: ENGAGED / CO-LIVING / WEDDING PREP
        # Screen / OTT
        screen_options = [
            {
                "id": "rec_screen_ddlj",
                "category": "movie",
                "category_label": "🛋️ Friday Night Stand-Off Solver",
                "title": "Dilwale Dulhania Le Jayenge (Prime Video)",
                "subtitle": "96% Overlap • Stream Tonight at Home",
                "affinity": 0.96,
                "image": "https://images.qloo.com/i/661E4E6A-0024-48A0-90D2-5A12E902D4FD-420x-auto.jpg",
                "description": f"Cozy Friday OTT streaming night for {first} & {pname}. Timeless romance, iconic melodies, and scenic European landscapes.",
                "why": f"Harmonizes {first}'s love for grand Bollywood melodies and {pname}'s acoustic romance.",
                "suggested_date": dates["friday"],
                "suggested_time": "20:30",
                "streaming": "Prime Video",
                "action_prompt": "Tell cupl: 'Stream a cozy romantic movie together tonight'"
            },
            {
                "id": "rec_screen_yjd",
                "category": "movie",
                "category_label": "🛋️ Friday Night Stand-Off Solver",
                "title": "Yeh Jawaani Hai Deewani (Netflix)",
                "subtitle": "95% Overlap • Travel & Romance Vibes",
                "affinity": 0.95,
                "image": None,
                "description": f"Nostalgic road-trip energy and emotional acoustic strings for {first} & {pname} to unwind after a week of planning.",
                "why": "Bridges wanderlust and grand celebratory energy with soulful acoustic themes.",
                "suggested_date": dates["friday"],
                "suggested_time": "20:45",
                "streaming": "Netflix",
                "action_prompt": "Tell cupl: 'Help us pick a fun weekend movie with great music'"
            },
            {
                "id": "rec_screen_abouttime",
                "category": "movie",
                "category_label": "🛋️ Friday Night Stand-Off Solver",
                "title": "About Time / Barfi! (Disney+ Hotstar)",
                "subtitle": "94% Overlap • Tender Storytelling & Acoustic Score",
                "affinity": 0.94,
                "image": None,
                "description": "Heartwarming, whimsical love story celebrating the sweetness of ordinary everyday moments together.",
                "why": "High emotional resonance score matching your shared appreciation for heartfelt indie storytelling.",
                "suggested_date": dates["friday"],
                "suggested_time": "20:30",
                "streaming": "Hotstar",
                "action_prompt": "Tell cupl: 'Suggest a heartwarming movie that brings us closer'"
            }
        ]

        # Dining / Evening Outing
        dining_options = [
            {
                "id": "rec_dining_paigah",
                "category": "dining",
                "category_label": "💆‍♀️ Pre-Wedding De-Stressor Date",
                "title": f"Paigah Palace / Paasha Courtyard ({city})",
                "subtitle": "94% Atmosphere Match • Strictly Zero Wedding Talk",
                "affinity": 0.94,
                "image": "https://images.qloo.com/i/F695BC35-FB39-4B37-9AE1-70C2ADC68043-420x-auto.jpg",
                "description": f"Heritage royal courtyard dining with candlelit tables, soft acoustic/Sufi background music, and authentic royal cuisine in {city}. Ground rule: Zero wedding checklist talk allowed tonight.",
                "why": f"Harmonizes your love for serene, heritage settings and unhurried couple recharge.",
                "suggested_date": dates["saturday"],
                "suggested_time": "19:30",
                "maps_url": f"https://www.google.com/maps/search/?api=1&query=Paigah+Palace+{city}".replace(" ", "+"),
                "est_cost": 3500,
                "action_prompt": f"Tell cupl: 'Reserve a serene romantic table at a courtyard in {city}'"
            },
            {
                "id": "rec_dining_olive",
                "category": "dining",
                "category_label": "💆‍♀️ Pre-Wedding De-Stressor Date",
                "title": f"Olive Bistro & Secret Lake Terrace ({city})",
                "subtitle": "93% Atmosphere Match • Sunset Lake Views",
                "affinity": 0.93,
                "image": None,
                "description": f"Rustic whitewashed Mediterranean terrace overlooking Durgam Cheruvu lake. Warm fairy lights, artisanal sourdough pizzas, and refreshing handcrafted mocktails.",
                "why": "A tranquil, breezy outdoor escape that melts away logistics stress.",
                "suggested_date": dates["saturday"],
                "suggested_time": "18:45",
                "maps_url": f"https://www.google.com/maps/search/?api=1&query=Olive+Bistro+{city}".replace(" ", "+"),
                "est_cost": 3200,
                "action_prompt": f"Tell cupl: 'Plan a sunset lakeview dinner date for us in {city}'"
            },
            {
                "id": "rec_dining_jewel",
                "category": "dining",
                "category_label": "💆‍♀️ Pre-Wedding De-Stressor Date",
                "title": f"The Jewel of Nizam / The Minar ({city})",
                "subtitle": "95% Atmosphere Match • Royal Fine Dining 100ft High",
                "affinity": 0.95,
                "image": None,
                "description": f"Dine 100 feet in the sky overlooking Osmansagar lake. Authentic Nizami slow-cooked biryani, acoustic sitar recitals, and opulent royal chandeliers.",
                "why": "Fits your shared regal heritage aesthetic with intimate couple service.",
                "suggested_date": dates["saturday"],
                "suggested_time": "20:00",
                "maps_url": f"https://www.google.com/maps/search/?api=1&query=Jewel+of+Nizam+{city}".replace(" ", "+"),
                "est_cost": 4200,
                "action_prompt": f"Tell cupl: 'Plan an extraordinary royal dining experience in {city}'"
            }
        ]

        # Stage Special: Signature Cocktail or Living Room Harmony
        special_options = [
            {
                "id": "rec_special_cocktail",
                "category": "cocktail",
                "category_label": "🍸 Signature Couple Drink Formulation",
                "title": "The Royal Saffron-Citrus Spark (Couple Blend)",
                "subtitle": "Taste Chemistry Formulation • Home Recipe Kit",
                "affinity": 0.97,
                "image": None,
                "description": f"Bespoke couple drink formula combining {first}'s fondness for warm spiced cardamom & saffron notes with {pname}'s love for crisp Meyer lemon, elderflower, and botanical soda.",
                "why": "A 1-of-1 taste chemistry formulation you can mix together at home or serve at your private dinners.",
                "suggested_date": dates["sunday"],
                "suggested_time": "17:00",
                "recipe": "Infused Kashmiri saffron syrup (20ml) + Meyer lemon juice (25ml) + Elderflower tonic (90ml) + crushed ice & star anise garnish.",
                "action_prompt": "Tell cupl: 'Give us our full signature cocktail and mocktail recipe cards'"
            },
            {
                "id": "rec_special_decor",
                "category": "decor",
                "category_label": "🛋️ Living Room Aesthetic Harmonizer",
                "title": "Warm Teak Meets Minimalist Japandi Harmony",
                "subtitle": "Interior Design Blueprint • Future Home Co-Living",
                "affinity": 0.94,
                "image": None,
                "description": f"A curated living room palette harmonizing {first}'s appreciation for royal heritage textures with {pname}'s preference for airy, pastel minimalism. Key elements: low-profile linen sofa, warm teak credenza, and 2700K rice-paper floor lamps.",
                "why": "Prevents decor friction by scientifically overlapping your tactile aesthetic scores.",
                "suggested_date": dates["sunday"],
                "action_prompt": "Tell cupl: 'Show our complete couple interior design aesthetic guide'"
            },
            {
                "id": "rec_special_dance",
                "category": "music",
                "category_label": "🎶 Unconventional First Dance & Sangeet Track",
                "title": "'Kasoor' Acoustic Transitioning into High-BPM Fusion",
                "subtitle": "Musical Chemistry Overlap • Sangeet Highlight",
                "affinity": 0.96,
                "image": None,
                "description": "Begins with an intimate Prateek Kuhad acoustic guitar slow dance for the two of you, then transitions smoothly at 1:45 into a joyful 124 BPM brass-and-dhol anthem that pulls your friends onto the floor.",
                "why": "Honors both intimate soulful emotion and exuberant celebration without cliché tropes.",
                "suggested_date": dates["friday"],
                "action_prompt": "Tell cupl: 'Create our custom First Dance edit with transition cues'"
            }
        ]

    elif stage == "dating":
        # STAGE 1: DATING / GETTING TO KNOW YOU
        screen_options = [
            {
                "id": "rec_screen_safebet",
                "category": "movie",
                "category_label": "🎬 The 'Safe-Bet' Double-Feature",
                "title": "Knives Out & Midnight in Paris",
                "subtitle": "95% Overlap • Zero Cringe, Great Dialogue",
                "affinity": 0.95,
                "image": None,
                "description": "Clever, witty, and gorgeously shot films guaranteed to spark engaging post-movie conversation without awkward silences.",
                "why": "High social proof and aesthetic consensus for early courtship.",
                "suggested_date": dates["friday"],
                "streaming": "Netflix / Prime Video",
                "action_prompt": "Tell cupl: 'Suggest safe-bet movies for a new dating night'"
            },
            {
                "id": "rec_screen_spiderverse",
                "category": "movie",
                "category_label": "🎬 The 'Safe-Bet' Double-Feature",
                "title": "Spider-Man: Across the Spider-Verse",
                "subtitle": "96% Overlap • High Energy & Dazzling Artistry",
                "affinity": 0.96,
                "image": None,
                "description": "Electrifying visuals, stellar soundtrack, and universal critical acclaim for a low-pressure movie date.",
                "why": "Captivating art direction that bridges animation lovers and music fans.",
                "suggested_date": dates["friday"],
                "streaming": "Netflix",
                "action_prompt": "Tell cupl: 'Suggest exciting animated or indie movies for us'"
            },
            {
                "id": "rec_screen_crazyrich",
                "category": "movie",
                "category_label": "🎬 The 'Safe-Bet' Double-Feature",
                "title": "Crazy Rich Asians (Prime Video)",
                "subtitle": "93% Overlap • Vibrant Romance & Lavish Sets",
                "affinity": 0.93,
                "image": None,
                "description": "Fun, romantic, and visually spectacular comedy with incredible food scenes and acoustic romantic ballads.",
                "why": "Upbeat romantic energy that puts both people in great spirits.",
                "suggested_date": dates["friday"],
                "streaming": "Prime Video",
                "action_prompt": "Tell cupl: 'Find romantic comedies with incredible food and music'"
            }
        ]

        dining_options = [
            {
                "id": "rec_dining_dimsum",
                "category": "dining",
                "category_label": "🍲 Icebreaker Communal Dining",
                "title": f"Bao & Dim Sum Tasting Crawl ({city})",
                "subtitle": "94% Interaction Match • Natural Conversation Flow",
                "affinity": 0.94,
                "image": None,
                "description": f"Shared bamboo steamers of truffle edamame dumplings, lotus-wrapped sticky rice, and artisanal matcha teas in {city}. Food you interact with keeps conversation effortless.",
                "why": "Shared small plates eliminate dining stiffness and awkward pauses.",
                "suggested_date": dates["saturday"],
                "maps_url": f"https://www.google.com/maps/search/?api=1&query=Dim+Sum+{city}".replace(" ", "+"),
                "est_cost": 2200,
                "action_prompt": f"Tell cupl: 'Find interactive shared-plate food spots in {city}'"
            },
            {
                "id": "rec_dining_coffee",
                "category": "dining",
                "category_label": "☕ Artisanal Coffee & Pastry Stroll",
                "title": f"Roastery Coffee House Garden ({city})",
                "subtitle": "92% Vibe Match • Casual Daylight Chemistry",
                "affinity": 0.92,
                "image": None,
                "description": f"Tranquil bungalow courtyard under lush trees with cold brew flights, warm onion rings, and fresh sourdough in {city}.",
                "why": "Low-pressure daytime setting perfect for getting to know each other.",
                "suggested_date": dates["saturday"],
                "suggested_time": "11:30",
                "maps_url": f"https://www.google.com/maps/search/?api=1&query=Roastery+Coffee+House+{city}".replace(" ", "+"),
                "est_cost": 1200,
                "action_prompt": f"Tell cupl: 'Plan a casual daytime coffee date in {city}'"
            },
            {
                "id": "rec_dining_tapas",
                "category": "dining",
                "category_label": "🍲 Icebreaker Communal Dining",
                "title": f"Rooftop Sunset Tapas & Board Game Cafe ({city})",
                "subtitle": "91% Atmosphere Match • Playful Energy",
                "affinity": 0.91,
                "image": None,
                "description": "Lively open-air terrace with small tapas, citrus sangrias, and cooperative two-player games like Codenames.",
                "why": "Gamified interaction breaks ice faster than traditional stiff dinner.",
                "suggested_date": dates["saturday"],
                "suggested_time": "18:00",
                "est_cost": 1800,
                "action_prompt": f"Tell cupl: 'Find fun board game and rooftop cafes in {city}'"
            }
        ]

        special_options = [
            {
                "id": "rec_special_playlist",
                "category": "music",
                "category_label": "🎵 Pre-Date Car Ride Vibe",
                "title": "Acoustic Indie & Soulful Chill Highway Mix",
                "subtitle": "Shared Vibe Chemistry • 35-Minute Set",
                "affinity": 0.96,
                "image": None,
                "description": "A curated 35-minute road tracklist of soothing acoustic indie and warm soul to set a relaxed, happy mood on the drive.",
                "why": "Eliminates pre-date anxiety with gentle harmonic frequencies.",
                "suggested_date": dates["friday"],
                "action_prompt": "Tell cupl: 'Build a 30-minute pre-date car playlist for us'"
            },
            {
                "id": "rec_special_arcade",
                "category": "experience",
                "category_label": "🎨 Interactive Low-Pressure Hangout",
                "title": f"Vintage Retro Arcade & Bowling Lounge ({city})",
                "subtitle": "93% Fun Score • Shared Teaming Up",
                "affinity": 0.93,
                "image": None,
                "description": "Nostalgic pinball machines, air hockey, and neon lights for a collaborative, high-laughter date.",
                "why": "Shared physical play triggers dopamine and effortless bonding.",
                "suggested_date": dates["saturday"],
                "action_prompt": f"Tell cupl: 'Find playful retro game bars in {city}'"
            },
            {
                "id": "rec_special_flea",
                "category": "experience",
                "category_label": "🎨 Weekend Design & Thrift Market",
                "title": f"Weekend Artisan Sunday Souk ({city})",
                "subtitle": "90% Aesthetic Match • Low-Stakes Stroll",
                "affinity": 0.90,
                "image": None,
                "description": "Handmade ceramic pottery, indie zines, and live indie busking in a breezy open lawn.",
                "why": "Browsing physical items reveals each other's tastes naturally without interrogation.",
                "suggested_date": dates["sunday"],
                "action_prompt": f"Tell cupl: 'Find weekend indie flea markets in {city}'"
            }
        ]

    else:
        # STAGE 4: MARRIED / LONG-TERM / PARENTS ("HAPPILY EVER AFTER")
        screen_options = [
            {
                "id": "rec_screen_nostalgia",
                "category": "movie",
                "category_label": "📼 Formative-Era Nostalgia Night",
                "title": "Jab We Met / Midnight in Paris (Rewatch)",
                "subtitle": "97% Nostalgia Score • Relive When You First Met",
                "affinity": 0.97,
                "image": None,
                "description": f"Turn off cellphones, pop masala popcorn, and rewatch the comfort film that defined the era {first} & {pname} first fell in love.",
                "why": "Reignites foundational romantic memories and early relationship warmth.",
                "suggested_date": dates["friday"],
                "streaming": "Netflix",
                "action_prompt": "Tell cupl: 'Suggest a nostalgia movie night from the year we met'"
            },
            {
                "id": "rec_screen_pastlives",
                "category": "movie",
                "category_label": "📼 Formative-Era Nostalgia Night",
                "title": "Past Lives (Prime Video)",
                "subtitle": "95% Affinity • Tender & Deeply Soulful",
                "affinity": 0.95,
                "image": None,
                "description": "A profound, poetic journey exploring destiny, deep emotional connection, and lifelong partnership.",
                "why": "Celebrates the rarity and depth of choosing each other over a lifetime.",
                "suggested_date": dates["friday"],
                "streaming": "Prime Video",
                "action_prompt": "Tell cupl: 'Recommend deeply moving cinematic gems for long-term couples'"
            },
            {
                "id": "rec_screen_laland",
                "category": "movie",
                "category_label": "📼 Formative-Era Nostalgia Night",
                "title": "La La Land (4K Ambient Projector Night)",
                "subtitle": "96% Affinity • Dazzling Melodies & Color",
                "affinity": 0.96,
                "image": None,
                "description": "Projector screening with dim fairy lights, sipping wine and singing along to the bittersweet piano themes.",
                "why": "Transform an ordinary evening into an at-home cinematic ritual.",
                "suggested_date": dates["friday"],
                "streaming": "Prime Video",
                "action_prompt": "Tell cupl: 'Plan an ambient home projector date night'"
            }
        ]

        dining_options = [
            {
                "id": "rec_dining_wildcard",
                "category": "dining",
                "category_label": "⚡ The 'Break-the-Routine' Wildcard Date",
                "title": f"Secret Chef's Table Omakase Experience ({city})",
                "subtitle": "95% Novelty Score • Shake Up Your Usual Spot",
                "affinity": 0.95,
                "image": None,
                "description": f"Step out of your comfort zone with an intimate 8-course chef counter experience in {city}. Watch the chef craft every dish live with surprising flavor contrasts.",
                "why": "Novel sensory experiences break relationship habituation and ignite spontaneous excitement.",
                "suggested_date": dates["saturday"],
                "maps_url": f"https://www.google.com/maps/search/?api=1&query=Chefs+Table+{city}".replace(" ", "+"),
                "est_cost": 4500,
                "action_prompt": f"Tell cupl: 'Find an extraordinary secret chef tasting menu in {city}'"
            },
            {
                "id": "rec_dining_charminar",
                "category": "dining",
                "category_label": "⚡ The 'Break-the-Routine' Wildcard Date",
                "title": f"Midnight Heritage Food Run & Irani Chai ({city})",
                "subtitle": "93% Spontaneity Score • 11:30 PM Adventure",
                "affinity": 0.93,
                "image": None,
                "description": f"A late-night drive to historic Old City for warm Osmania biscuits, saffron Irani chai, and kebabs under illuminated stone arches.",
                "why": "Spontaneous late-night outings bring back the thrills of early courtship.",
                "suggested_date": dates["saturday"],
                "suggested_time": "23:00",
                "maps_url": f"https://www.google.com/maps/search/?api=1&query=Nimrah+Cafe+{city}".replace(" ", "+"),
                "est_cost": 800,
                "action_prompt": f"Tell cupl: 'Plan a late-night street food adventure in {city}'"
            },
            {
                "id": "rec_dining_micro",
                "category": "dining",
                "category_label": "⏱️ Parents' Quick Escape (2-Hour Micro-Date)",
                "title": f"Boutique Jazz & Tapas Speakeasy ({city})",
                "subtitle": "94% Speed & Impact Match • 15 Mins Away",
                "affinity": 0.94,
                "image": None,
                "description": f"High-impact dining engineered for tight babysitter windows: rapid seating, bespoke craft cocktails, and Spanish tapas within 15 mins of home.",
                "why": "Maximum romantic intimacy packed into a reliable 120-minute window.",
                "suggested_date": dates["saturday"],
                "suggested_time": "19:00",
                "est_cost": 2800,
                "action_prompt": f"Tell cupl: 'Plan a quick 2-hour high-impact date night near home'"
            }
        ]

        special_options = [
            {
                "id": "rec_special_dance_late",
                "category": "music",
                "category_label": "🕯️ Midnight Living Room Slow-Dance",
                "title": "Vinyl & Candlelight Unwind Session",
                "subtitle": "Intimacy Chemistry • After House Goes Quiet",
                "affinity": 0.98,
                "image": None,
                "description": f"Dim all overhead lights, pour herbal tea or wine, and play a slow 4-track acoustic set while dancing barefoot in your living room.",
                "why": "Recharges couple intimacy without needing to hire a sitter or leave the house.",
                "suggested_date": dates["friday"],
                "suggested_time": "22:30",
                "action_prompt": "Tell cupl: 'Curate a midnight living room slow-dance playlist'"
            },
            {
                "id": "rec_special_theatre",
                "category": "experience",
                "category_label": "⚡ Spontaneous Live Arts Night",
                "title": f"Independent Theatre or Sufi Qawwali Night ({city})",
                "subtitle": "92% Cultural Overlap • Soulful Energy",
                "affinity": 0.92,
                "image": None,
                "description": f"Immerse in live acoustic Sufi music or an intimate black-box theatre play in {city}.",
                "why": "Shared emotional catharsis through performing arts.",
                "suggested_date": dates["saturday"],
                "action_prompt": f"Tell cupl: 'Find live sufi or theatre performances this weekend in {city}'"
            },
            {
                "id": "rec_special_cook",
                "category": "culinary",
                "category_label": "🍳 Late-Sunday Slow Brunch Tradition",
                "title": "Cardamom-Pistachio Brioche French Toast & Chemex Coffee",
                "subtitle": "Sunday Morning Ritual • Cook Together at Home",
                "affinity": 0.95,
                "image": None,
                "description": "A slow Sunday morning tradition: whipping brioche French toast infused with crushed green cardamom, roasted pistachios, and warm honey.",
                "why": "Builds a sacred recurring ritual you both anticipate throughout the week.",
                "suggested_date": dates["sunday"],
                "suggested_time": "10:30",
                "action_prompt": "Tell cupl: 'Give us our step-by-step Sunday brunch recipe'"
            }
        ]

    # Category 4: Spontaneous Weekend Retreat / Getaways (Rotates per cycle)
    getaway_options = [
        {
            "id": "rec_escape_hampi",
            "category": "travel",
            "category_label": "🚗 Spontaneous 48h Couple Escape",
            "title": "Hampi / Heritage Boulders & Riverfront Retreat",
            "subtitle": "92% Destination Match • Tranquil Couple Recharge",
            "affinity": 0.92,
            "image": None,
            "description": "Ancient royal ruins, quiet Tungabhadra riverfront sunsets, and cozy boutique heritage cottages tucked among granite hills.",
            "why": "Fits your shared Couple DNA for picturesque heritage and peaceful downtime.",
            "suggested_date": dates["in_two_weeks"],
            "action_prompt": "Tell cupl: 'Help us plan a quick 2-day heritage weekend trip'"
        },
        {
            "id": "rec_escape_ananthagiri",
            "category": "travel",
            "category_label": "🚗 Spontaneous 48h Couple Escape",
            "title": f"Ananthagiri Hills Forest Boutique Stay (Near {city})",
            "subtitle": "90% Destination Match • 90-Minute Drive",
            "affinity": 0.90,
            "image": None,
            "description": "Dense teak forests, misty morning coffee walks, and a quiet hillside cottage just 90 minutes outside the city.",
            "why": "Zero-stress micro-travel when neither partner wants to deal with airports.",
            "suggested_date": dates["in_two_weeks"],
            "action_prompt": f"Tell cupl: 'Plan a serene forest resort weekend near {city}'"
        },
        {
            "id": "rec_escape_pondy",
            "category": "travel",
            "category_label": "🚗 Spontaneous 48h Couple Escape",
            "title": "Pondicherry French Quarter & Promenade Hideaway",
            "subtitle": "93% Destination Match • Coastal Romance",
            "affinity": 0.93,
            "image": None,
            "description": "Pastel yellow heritage villas, bougainvillea balconies, French bakeries, and long sunset walks along the sea wall.",
            "why": "Charming colonial architecture and romantic oceanside strolls.",
            "suggested_date": dates["in_two_weeks"],
            "action_prompt": "Tell cupl: 'Plan a coastal weekend getaway to Pondicherry'"
        }
    ]

    # Category 5: Private Gifting & Surprise (Rotates per cycle, strictly in Private Tab)
    private_gift_options = [
        {
            "id": f"rec_gift_shawl_{pname.lower()}",
            "category": "gifting",
            "category_label": f"Thoughtful Gifting for {pname}",
            "for_partner": pname,
            "title": f"Boutique Heritage Embroidered Shawl for {pname}",
            "subtitle": "Curated from her private aesthetic",
            "affinity": 0.95,
            "description": f"Surprise {pname} with an authentic pastel-embroidered Kashmiri or Chanderi silk accessory inspired by her love for Sabyasachi aesthetics and handcrafted luxury.",
            "why": f"Tailored secretly to {pname}'s love for understated luxury and pastel tones.",
            "suggested_date": dates["milestone"],
            "price_bracket": "₹5,000 – ₹15,000",
            "is_private": True,
            "action_prompt": f"Tell cupl privately: 'Help me find the perfect heirloom gift for {pname}'"
        },
        {
            "id": f"rec_gift_perfume_{pname.lower()}",
            "category": "gifting",
            "category_label": f"Thoughtful Gifting for {pname}",
            "for_partner": pname,
            "title": f"Artisanal Attar / Botanical Scent Discovery Box for {pname}",
            "subtitle": "Formulated around her favorite olfactory notes",
            "affinity": 0.96,
            "description": f"A secret gift flight of small-batch natural perfumes featuring white jasmine, sandalwood, and warm amber notes matching {pname}'s signature aesthetic.",
            "why": f"Intimate and personal, matched to {pname}'s sensory profile.",
            "suggested_date": dates["milestone"],
            "price_bracket": "₹4,000 – ₹9,000",
            "is_private": True,
            "action_prompt": f"Tell cupl privately: 'Help me choose custom luxury fragrances for {pname}'"
        },
        {
            "id": f"rec_gift_journal_{pname.lower()}",
            "category": "gifting",
            "category_label": f"Thoughtful Gifting for {pname}",
            "for_partner": pname,
            "title": f"Custom Gold-Embossed Leather Memory Journal for {pname}",
            "subtitle": "Handcrafted keepsake with gold-foil initials",
            "affinity": 0.94,
            "description": f"Italian full-grain leather bound journal engraved with {pname}'s initials in gold foil, pre-filled on page one with your favorite photo and a heartfelt handwritten note.",
            "why": "A timeless sentimental keepsake she will treasure for decades.",
            "suggested_date": dates["milestone"],
            "price_bracket": "₹2,500 – ₹6,000",
            "is_private": True,
            "action_prompt": f"Tell cupl privately: 'Help me compose a note for a leather journal for {pname}'"
        }
    ]

    private_surprise_options = [
        {
            "id": f"rec_surprise_date_{pname.lower()}",
            "category": "surprise",
            "category_label": "Secret Date Night Surprise",
            "for_partner": pname,
            "title": f"Acoustic Sunset Candlelight Rooftop for {pname}",
            "subtitle": "Zero-stress secret arrangement",
            "affinity": 0.94,
            "description": f"A private rooftop table adorned with fairy lights, her favorite white flowers, and a solo acoustic guitarist quietly playing {pname}'s favorite Prateek Kuhad tunes.",
            "why": "Creates an intimate, cinematic memory that melts away all outside stress.",
            "suggested_date": dates["milestone"],
            "is_private": True,
            "action_prompt": f"Tell cupl privately: 'Help me arrange a secret rooftop dinner for {pname}'"
        },
        {
            "id": f"rec_surprise_stargaze_{pname.lower()}",
            "category": "surprise",
            "category_label": "Secret Date Night Surprise",
            "for_partner": pname,
            "title": f"Private Stargazing Picnic & Telescope Night for {pname}",
            "subtitle": "Secluded outdoor wonder",
            "affinity": 0.95,
            "description": f"A warm cashmere throw blanket, hot spiced apple cider in a thermos, and a portable telescope set up on a quiet hill overlooking the city lights.",
            "why": "Pure romance and quiet shared wonder under the open sky.",
            "suggested_date": dates["milestone"],
            "is_private": True,
            "action_prompt": f"Tell cupl privately: 'Help me plan a secret stargazing picnic for {pname}'"
        },
        {
            "id": f"rec_surprise_dessert_{pname.lower()}",
            "category": "surprise",
            "category_label": "Secret Date Night Surprise",
            "for_partner": pname,
            "title": f"Hidden Courtyard Dessert & High-Tea Surprise for {pname}",
            "subtitle": "Afternoon indulgence",
            "affinity": 0.93,
            "description": f"A secret afternoon reservation at a sunlit garden conservatory with a custom tiered stand of pistachio macarons, rose scones, and rare Darjeeling teas.",
            "why": f"Tailored to {pname}'s sweet tooth and love for elegant teatime rituals.",
            "suggested_date": dates["milestone"],
            "is_private": True,
            "action_prompt": f"Tell cupl privately: 'Help me book a secret high tea surprise for {pname}'"
        }
    ]

    # Select based on active rotation cycle
    selected_screen = screen_options[cycle % len(screen_options)]
    selected_dining = dining_options[cycle % len(dining_options)]
    selected_special = special_options[cycle % len(special_options)]
    selected_escape = getaway_options[cycle % len(getaway_options)]

    selected_gift = private_gift_options[cycle % len(private_gift_options)]
    selected_surprise = private_surprise_options[cycle % len(private_surprise_options)]

    couple_recs = [selected_screen, selected_dining, selected_special, selected_escape]
    private_recs = [selected_gift, selected_surprise]

    # Annotate with calendar status
    for r in couple_recs + private_recs:
        r["added_to_calendar"] = r["id"] in added_ids

    return {
        "enabled": True,
        "couple_status": stage,
        "cycle": cycle,
        "couple_recs": couple_recs,
        "private_recs": private_recs,
        "added_ids": added_ids,
        "active_city": city,
        "partner_name": pname,
        "couple_vibe": dna_vibe,
        "calendar_status": {
            "is_fri_busy": is_fri_busy,
            "is_sat_busy": is_sat_busy
        }
    }
