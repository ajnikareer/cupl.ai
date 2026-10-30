import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("."))

from backend.app.db import db, new_id, now_iso
from backend.app.services import calendar_svc

async def full_cleanup():
    print("Starting full database cleanup of old test accounts...")
    
    # 1. Accounts to wipe
    uids_to_wipe = ["ajnikarnarayan", "vyawahare40", "cupl_star_1", "cupl_star_2", "groom_narayan"]
    
    for uid in uids_to_wipe:
        print(f"Purging user {uid}...")
        # purge turns
        async for tsnap in db.collection(f"conversations/{uid}/turns").stream():
            await db.document(f"conversations/{uid}/turns/{tsnap.id}").delete()
        # purge conv
        await db.document(f"conversations/{uid}").delete()
        # purge tastes
        async for tsnap in db.collection(f"users/{uid}/tastes").stream():
            await db.document(f"users/{uid}/tastes/{tsnap.id}").delete()
        # purge user doc
        await db.document(f"users/{uid}").delete()

    # 2. Purge old couples & spaces
    couples_to_wipe = ["c_cupl_star", "c_groom_demo"]
    for cid in couples_to_wipe:
        async for snap in db.collection("spaces").where("couple_id", "==", cid).stream():
            sid = snap.id
            async for p in db.collection(f"spaces/{sid}/plans").stream():
                await db.document(f"spaces/{sid}/plans/{p.id}").delete()
            await db.document(f"spaces/{sid}").delete()
        async for cal in db.collection("calendar_items").where("couple_id", "==", cid).stream():
            await db.document(f"calendar_items/{cal.id}").delete()
        async for sp in db.collection("surprises").where("couple_id", "==", cid).stream():
            await db.document(f"surprises/{sp.id}").delete()
        await db.document(f"couples/{cid}").delete()

    print("Old accounts wiped completely!")

    # 3. Create Fresh Groom Showcase
    uid1 = "groom_narayan"
    cid = "c_groom_demo"
    space_id = "s_narayan_wedding"
    name1 = "Narayan"
    name2 = "Amruta"

    print(f"Creating fresh Groom Demo profile for {name1} (Planning with {name2})...")

    # Groom user
    groom_doc = {
        "uid": uid1,
        "name": name1,
        "name_confirmed": True,
        "name_from_provider": True,
        "email": "narayan@cupl.app",
        "couple_id": cid,
        "active_space_id": space_id,
        "profile": {
            "partner_name": name2,
            "how_met": "Met at an independent coffee roastery",
            "heritage": "Royal North Indian & Awadhi",
            "tradition": "Hindu Vedic",
            "state": "Hyderabad",
            "country": "India",
            "greeted": True,
            "invite_offered": False,
            "partner_welcomed": False
        },
        "created_at": now_iso()
    }
    await db.document(f"users/{uid1}").set(groom_doc)

    # Couple doc (only 1 member: Narayan! Amruta is not onboarded yet!)
    couple_doc = {
        "id": cid,
        "members": [uid1],
        "status": "engaged",
        "recommends_enabled": True,
        "recommends_cycle": 0,
        "created_at": now_iso(),
        "dna": {
            "vibe": "Royal North Indian Grandeur awaiting Bride's Harmony",
            "description": f"{name1}'s tastes are locked in. Amruta's aesthetic will be harmonized as soon as she joins!",
            "shared": [
                {"name": "Acoustic Sufi & Soulful Melodies", "category": "music"},
                {"name": "Royal Awadhi Cuisine", "category": "dining"},
                {"name": "Sabyasachi Raw Silk Weaves", "category": "fashion"}
            ]
        }
    }
    await db.document(f"couples/{cid}").set(couple_doc)

    # Groom's 4 Tastes
    groom_tastes = [
        {"text": "Arijit Singh & Soulful Bollywood", "category": "music", "sentiment": 1.0, "visibility": "shared"},
        {"text": "Acoustic Sufi Melodies & Qawwali", "category": "music", "sentiment": 0.95, "visibility": "shared"},
        {"text": "Royal Awadhi Biryani & Dum Pukht", "category": "dining", "sentiment": 0.9, "visibility": "shared"},
        {"text": "Sabyasachi Heritage Raw Silk Sherwanis", "category": "fashion", "sentiment": 0.95, "visibility": "shared"}
    ]
    for t in groom_tastes:
        await db.document(f"users/{uid1}/tastes/{new_id('t')}").set({
            **t, "uid": uid1, "confidence": 0.95, "created_at": now_iso()
        })

    # Groom's Wedding Space (Awaiting Bride - NO plan woven yet so Gatekeeper triggers!)
    space_doc = {
        "id": space_id,
        "couple_id": cid,
        "type": "wedding",
        "title": f"{name1} & {name2}'s Wedding",
        "city": "Hyderabad",
        "start_date": "2026-12-18",
        "end_date": "2026-12-20",
        "budget": 2500000.0,
        "currency": "INR",
        "guests": 400,
        "ceremonies": ["Haldi", "Sangeet", "Wedding", "Reception"],
        "state": "planned",
        "active_plan_version": None,  # No plan yet! Triggers Gatekeeper!
        "created_by": uid1,
        "created_at": now_iso()
    }
    await db.document(f"spaces/{space_id}").set(space_doc)

    # 2 Everyday Plans in Plans tab
    plans = [
        {
            "title": "Friday Movie Night: Zindagi Na Milegi Dobara",
            "subtitle": "Living Room OTT Streaming & Spanish Tapas",
            "category": "movie",
            "date": "2026-11-06",
            "time": "20:30",
            "description": f"Cozy evening streaming date for {name1} & {name2} with Spanish tapas.",
            "is_private": False
        },
        {
            "title": "Pre-Wedding De-Stressor Date at Olive Bistro",
            "subtitle": "Lakeside Terrace • Candlelit Dinner",
            "category": "dining",
            "date": "2026-11-14",
            "time": "19:45",
            "description": "Candlelit dinner overlooking Durgam Cheruvu lake. Fresh artisanal sourdough pizza.",
            "maps_url": "https://maps.google.com/?q=Olive+Bistro+Hyderabad",
            "is_private": False
        }
    ]
    for p in plans:
        await calendar_svc.add_calendar_item(groom_doc, p)

    # Clean initial conversation
    chat_turns = [
        {
            "id": "turn_1",
            "role": "agent",
            "text": f"Hello {name1}! 💕 Welcome to cupl AI — your AI concierge for life together.\n\nI am here to help you and {name2} navigate life's big milestones and everyday dates with deep cultural taste intelligence.\n\nI can assist you with:\n1. 💍 Milestone Events (Weddings, Anniversaries)\n2. 🍿 Everyday Plans (Friday movie nights, dinner dates)\n3. ✨ Weekly Lifestyle Recommendations (tailored by Qloo Cultural IQ)\n\nTo begin, what musical vibe and culinary flavors make you feel most alive?",
            "created_at": now_iso()
        },
        {
            "id": "turn_2",
            "role": "user",
            "text": "I love grand Awadhi biryani, Arijit Singh melodies, and majestic heritage architecture. We are planning a 400-guest wedding in Hyderabad in December.",
            "created_at": now_iso()
        },
        {
            "id": "turn_3",
            "role": "agent",
            "text": f"Captured, {name1}! 👑\n\nI've saved your Awadhi cuisine roots, Sufi musical tastes, and 400-guest venue parameters in your profile.\n\nBefore I weave your full masterplan, cupl's **Couple Gatekeeper** requires {name2} to join and share her aesthetic so both your worlds are harmonized! Shall I create an invite link for her?",
            "created_at": now_iso()
        }
    ]
    await db.document(f"conversations/{uid1}").set({
        "turn_count": 3,
        "summary": f"{name1} is planning a 400-guest wedding in Hyderabad. Tastes captured. Awaiting {name2} to join.",
        "turns": chat_turns,
        "updated_at": now_iso()
    })

    print("\n[SUCCESS] Clean Groom Demo Profile created!")
    print(f" - Login Token: dev-{uid1}")
    print(f" - Groom Name: {name1}")
    print(f" - Partner Name: {name2}")
    print(f" - Event Space: {space_id} (Gatekeeper Active: Awaiting Bride!)")

if __name__ == "__main__":
    asyncio.run(full_cleanup())
