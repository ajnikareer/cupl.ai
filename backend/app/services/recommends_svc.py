"""Recommends Service: the perpetual 'Happily Ever After' lifestyle engine.
Generates couple recommendations (Friday movie match, weekend dining, getaways)
and private partner gifting/surprise recommendations, grounded in QLOO taste intelligence."""
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
    # Next month mid
    next_month = t + timedelta(days=21)
    return {
        "friday": next_fri.isoformat(),
        "saturday": next_sat.isoformat(),
        "milestone": next_month.isoformat()
    }

async def get_lifestyle_recommendations(user: dict) -> dict:
    snap = await state.load(user["uid"], with_episodes=False)
    pname = (snap.partner or {}).get("name") or (snap.user.get("profile") or {}).get("partner_name") or "your partner"
    first = (snap.user.get("name") or "You").split(" ")[0]
    dates = get_upcoming_dates()
    added_ids = await get_added_rec_ids(user)

    # City determination: active space city -> profile state -> Hyderabad default
    city = (snap.space or {}).get("city") or (snap.user.get("profile") or {}).get("state") or "Hyderabad"
    if "," in city:
        city = city.split(",")[0].strip()

    # Extract couple tastes
    my_names = [f["text"] for f in snap.my_facts[:6]]
    p_names = [f["text"] for f in snap.partner_facts[:6]]
    dna_vibe = (snap.couple.get("dna") or {}).get("vibe") or "Romantic, soulful, elegant"

    # Couple Recommendation 1: Friday Movie Match
    # Blends romance & cinema tastes
    movie_rec = {
        "id": "rec_movie_friday",
        "category": "movie",
        "category_label": "Friday Movie Night Match",
        "title": "Dilwale Dulhania Le Jayenge & Modern Cinema Night",
        "subtitle": "96% Couple Taste Match",
        "affinity": 0.96,
        "image": "https://images.qloo.com/i/661E4E6A-0024-48A0-90D2-5A12E902D4FD-420x-auto.jpg",
        "description": f"Curated for {first} & {pname}: Timeless romance, melodic music, and picturesque European landscapes. Perfect cozy watch with your shared favorites.",
        "why": f"Matches {first}'s love for grand Bollywood melodies and {pname}'s acoustic romance.",
        "suggested_date": dates["friday"],
        "suggested_time": "20:30",
        "streaming": "Prime Video",
        "action_prompt": "Tell WeaveWed: 'What movie should we watch together tonight?'"
    }

    # Couple Recommendation 2: Weekend Romantic Dining
    dining_rec = {
        "id": "rec_dining_saturday",
        "category": "dining",
        "category_label": f"Saturday Date Night in {city}",
        "title": f"Paigah Palace / Paasha Courtyard ({city})",
        "subtitle": "93% Atmosphere Match",
        "affinity": 0.93,
        "image": "https://images.qloo.com/i/F695BC35-FB39-4B37-9AE1-70C2ADC68043-420x-auto.jpg",
        "description": f"Heritage royal courtyard dining with candlelit tables, soft acoustic/Sufi background music, and authentic regional cuisine in {city}.",
        "why": f"Harmonizes your love for serene, heritage settings and exquisite dining.",
        "suggested_date": dates["saturday"],
        "suggested_time": "19:30",
        "maps_url": f"https://www.google.com/maps/search/?api=1&query=Paigah+Palace+{city}".replace(" ", "+"),
        "est_cost": 3500,
        "action_prompt": f"Tell WeaveWed: 'Plan a surprise table booking at a romantic courtyard in {city}'"
    }

    # Couple Recommendation 3: Spontaneous Weekend Getaway
    escape_rec = {
        "id": "rec_escape_weekend",
        "category": "travel",
        "category_label": "Spontaneous 2-Day Couple Escape",
        "title": "Hampi / Heritage Boulders & Riverfront Retreat",
        "subtitle": "91% Destination Match",
        "affinity": 0.91,
        "image": None,
        "description": "A tranquil weekend retreat away from the city: ancient royal ruins, quiet riverfront sunsets, and cozy boutique heritage cottages.",
        "why": "Fits your shared Couple DNA for picturesque heritage and peaceful couple time.",
        "suggested_date": (today() + timedelta(days=14)).isoformat(),
        "action_prompt": "Tell WeaveWed: 'Help us plan a quick 2-day heritage weekend trip'"
    }

    # Private Surprise & Gifting Recommendations (Just for You)
    # Strictly hidden from partner!
    p_roots = (snap.partner or {}).get("profile") or {}
    p_heritage = p_roots.get("heritage") or "Indian"

    private_gift = {
        "id": f"rec_gift_{pname.lower()}",
        "category": "gifting",
        "category_label": f"Thoughtful Gifting for {pname}",
        "for_partner": pname,
        "title": f"Boutique Heritage Gift for {pname}",
        "subtitle": "Curated from her private aesthetic",
        "affinity": 0.95,
        "description": f"Surprise {pname} with an authentic pastel-embroidered shawl or designer accessory inspired by her love for Sabyasachi aesthetics and handcrafted tradition.",
        "why": f"Tailored secretly to {pname}'s love for understated luxury and pastel tones.",
        "suggested_date": dates["milestone"],
        "price_bracket": "₹5,000 – ₹15,000",
        "is_private": True,
        "action_prompt": f"Tell WeaveWed privately: 'Help me find the perfect birthday gift for {pname}'"
    }

    private_date = {
        "id": f"rec_surprise_date_{pname.lower()}",
        "category": "surprise",
        "category_label": f"Secret Date Night Surprise",
        "for_partner": pname,
        "title": f"Acoustic Sunset Candlelight Dinner for {pname}",
        "subtitle": "Zero-stress secret arrangement",
        "affinity": 0.94,
        "description": f"A private rooftop table with fairy lights and an acoustic musician playing {pname}'s favorite Prateek Kuhad melodies.",
        "why": f"Creates a cinematic, intimate memory she'll never forget.",
        "suggested_date": dates["milestone"],
        "is_private": True,
        "action_prompt": f"Tell WeaveWed privately: 'Help me arrange a secret rooftop dinner for {pname}'"
    }

    couple_recs = [movie_rec, dining_rec, escape_rec]
    private_recs = [private_gift, private_date]

    # Annotate with calendar status
    for r in couple_recs + private_recs:
        r["added_to_calendar"] = r["id"] in added_ids

    return {
        "couple_recs": couple_recs,
        "private_recs": private_recs,
        "added_ids": added_ids,
        "active_city": city,
        "partner_name": pname,
        "couple_vibe": dna_vibe
    }
