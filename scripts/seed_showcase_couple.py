import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath("."))

from backend.app.db import db, new_id, now_iso
from backend.app.services import dna, calendar_svc

async def create_showcase(name1="Narayan", name2="Amruta", prefix="cupl_star"):
    uid1 = f"{prefix}_1"
    uid2 = f"{prefix}_2"
    cid = f"c_{prefix}"
    space_id = f"s_{prefix}_wedding"
    
    print(f"Creating pristine showcase couple: {name1} & {name2}...")

    # 1. User 1
    u1_doc = {
        "uid": uid1,
        "name": name1,
        "name_confirmed": True,
        "name_from_provider": True,
        "email": f"{name1.lower()}@{prefix}.app",
        "couple_id": cid,
        "active_space_id": space_id,
        "profile": {
            "partner_name": name2,
            "how_met": "Met at an independent coffee roastery in Bandra",
            "heritage": "Royal North Indian & Awadhi",
            "tradition": "Hindu (Vedic rituals with modern elegance)",
            "state": "Hyderabad",
            "country": "India",
            "greeted": True,
            "invite_offered": True,
            "partner_welcomed": True
        },
        "created_at": now_iso()
    }
    await db.document(f"users/{uid1}").set(u1_doc)

    # 2. User 2
    u2_doc = {
        "uid": uid2,
        "name": name2,
        "name_confirmed": True,
        "name_from_provider": True,
        "email": f"{name2.lower()}@{prefix}.app",
        "couple_id": cid,
        "active_space_id": space_id,
        "profile": {
            "partner_name": name1,
            "how_met": "Met at an independent coffee roastery in Bandra",
            "heritage": "Maharashtrian & Peshwai",
            "tradition": "Hindu (Traditional Maharashtrian Sakharpuda & Lagna)",
            "state": "Hyderabad",
            "country": "India",
            "greeted": True,
            "invite_offered": True,
            "partner_welcomed": True
        },
        "created_at": now_iso()
    }
    await db.document(f"users/{uid2}").set(u2_doc)

    # 3. Couple Document
    couple_doc = {
        "id": cid,
        "members": [uid1, uid2],
        "status": "engaged",
        "recommends_enabled": True,
        "recommends_cycle": 0,
        "created_at": now_iso(),
        "dna": {
            "vibe": "Royal Heritage elegance meets soulful acoustic intimacy",
            "description": f"A rich cultural tapestry blending {name1}'s appreciation for regal grandeur with {name2}'s love for understated pastel minimalism and organic textures.",
            "shared": [
                {"name": "Acoustic Sufi & Soulful Melodies", "category": "music"},
                {"name": "Lakeside Sunset Dining", "category": "dining"},
                {"name": "Zindagi Na Milegi Dobara", "category": "movie"},
                {"name": "Barfi!", "category": "movie"},
                {"name": "Sabyasachi Heritage Weaves", "category": "fashion"},
                {"name": "Amalfi Coast & Southern Italy", "category": "travel"},
                {"name": "Artisanal Coffee & Slow Mornings", "category": "lifestyle"}
            ],
            "cultural_harmony": {
                "title": "Maharashtrian-North Indian Royal Fusion",
                "summary": f"Harmonizing {name2}'s vibrant yellow Haldi rituals and Paithani silk sarees with {name1}'s regal Baraat brass curves and Awadhi dum cuisine.",
                "ideas": [
                    {"category": "Ceremony", "title": "Bilingual Vows & Royal Mandap", "description": "Traditional Vedic chants paired with personalized Hindi and Marathi vow exchanges under a 2700K floral canopy."},
                    {"category": "Catering", "title": "Dual-Heritage Gastronomy Counters", "description": "Parallel live culinary stations: Awadhi Zafrani Biryani alongside authentic Kolhapuri Pandhra Rassa & Puran Poli."},
                    {"category": "Sangeet", "title": "Multi-Generational Sangeet Music Curve", "description": "100 BPM acoustic folk transition into 128 BPM Bollywood brass and Marathi Dhol-Tasha finale."}
                ]
            }
        }
    }
    await db.document(f"couples/{cid}").set(couple_doc)

    # 4. Tastes for User 1
    tastes_u1 = [
        {"text": "Arijit Singh & Soulful Bollywood", "category": "music", "sentiment": 1.0, "visibility": "shared"},
        {"text": "Prateek Kuhad Acoustic Folk", "category": "music", "sentiment": 0.9, "visibility": "shared"},
        {"text": "Dilwale Dulhania Le Jayenge & Classic Cinema", "category": "movie", "sentiment": 0.9, "visibility": "shared"},
        {"text": "Zindagi Na Milegi Dobara", "category": "movie", "sentiment": 1.0, "visibility": "shared"},
        {"text": "Royal Awadhi & Mughlai Cuisine", "category": "dining", "sentiment": 0.9, "visibility": "shared"},
        {"text": "Sabyasachi Royal Sherwanis & Raw Silk", "category": "fashion", "sentiment": 0.95, "visibility": "shared"},
        {"text": "Lake Como & Scenic European Lakes", "category": "travel", "sentiment": 0.9, "visibility": "shared"},
        {"text": "Woody Oud & Amber Fragrances", "category": "fashion", "sentiment": 0.9, "visibility": "private"}
    ]
    for t in tastes_u1:
        await db.document(f"users/{uid1}/tastes/{new_id('t')}").set({
            **t, "uid": uid1, "confidence": 0.95, "created_at": now_iso()
        })

    # 5. Tastes for User 2
    tastes_u2 = [
        {"text": "Jasleen Royal & Indie Acoustic Strings", "category": "music", "sentiment": 1.0, "visibility": "shared"},
        {"text": "Coldplay & Ambient Stadium Ballads", "category": "music", "sentiment": 0.9, "visibility": "shared"},
        {"text": "Barfi! & Tender Storytelling", "category": "movie", "sentiment": 1.0, "visibility": "shared"},
        {"text": "About Time & Whimsical Romance", "category": "movie", "sentiment": 0.95, "visibility": "shared"},
        {"text": "Lakeside Mediterranean & Farm-to-Table", "category": "dining", "sentiment": 0.9, "visibility": "shared"},
        {"text": "Anita Dongre Handcrafted Pastel Lehengas", "category": "fashion", "sentiment": 0.95, "visibility": "shared"},
        {"text": "Kyoto Zen Gardens & Peaceful Bamboo Groves", "category": "travel", "sentiment": 0.9, "visibility": "shared"},
        {"text": "Artisanal Jasmine & French White Florals", "category": "fashion", "sentiment": 0.95, "visibility": "private"}
    ]
    for t in tastes_u2:
        await db.document(f"users/{uid2}/tastes/{new_id('t')}").set({
            **t, "uid": uid2, "confidence": 0.95, "created_at": now_iso()
        })

    # 6. Event Space (The Royal Wedding)
    space_doc = {
        "id": space_id,
        "couple_id": cid,
        "type": "wedding",
        "title": f"{name1} & {name2}'s Royal Wedding",
        "city": "Hyderabad",
        "start_date": "2026-12-18",
        "end_date": "2026-12-20",
        "budget": 2500000.0,
        "currency": "INR",
        "guests": 400,
        "ceremonies": ["Haldi", "Mehendi", "Sangeet", "Wedding", "Reception"],
        "destination": "Europe",
        "state": "planned",
        "active_plan_version": 1,
        "created_by": uid1,
        "created_at": now_iso()
    }
    await db.document(f"spaces/{space_id}").set(space_doc)

    # 7. Wedding Plan Sections (5 Core Blueprint Sections with Recommends-Grade Metadata)
    plan_doc = {
        "version": 1,
        "status": "ready",
        "created_at": now_iso(),
        "sections": [
            {
                "key": "venue",
                "title": "Venue Shortlist",
                "status": "ready",
                "summary": f"Curated Hyderabad palaces & luxury banquet estates matching {name1} and {name2}'s 400-guest scale, speech acoustics, and 35% budget allocation envelope.",
                "items": [
                    {
                        "id": "v1",
                        "title": "Taj Falaknuma Palace (Durbar Hall & 101-Seater)",
                        "affinity": 0.98,
                        "est_cost": 850000,
                        "loved_by_both": True,
                        "status": "liked",
                        "description": "Grand Nizam heritage palace perched 2,000 feet above Hyderabad. Venetian chandeliers, Italian marble courtyards, and royal carriage arrival.",
                        "capacity_check": "Capacity: 600 guests (Comfortably accommodates your 400 guests with ~50% buffer)",
                        "budget_breakdown": "Est. Rental: ₹4.5L | F&B Target: ₹1,650/plate within your ₹875,000 venue envelope",
                        "anti_clash_check": "Clash-Free: Independent ceremony lawns guarantee acoustic separation from neighboring banquets",
                        "heritage_origin": "Nizami & Royal Indian Heritage",
                        "why": [
                            f"Matches {name1}'s dream of majestic royal architecture and regal arrival procession",
                            f"Provides {name2}'s preferred open-air courtyards under starry skies with quiet garden corners"
                        ],
                        "maps_url": "https://maps.google.com/?q=Taj+Falaknuma+Palace+Hyderabad"
                    },
                    {
                        "id": "v2",
                        "title": "Best Western Ashoka (Hotel & AC Banquets)",
                        "affinity": 0.94,
                        "est_cost": 350000,
                        "loved_by_both": False,
                        "status": "suggested",
                        "description": "Central 3-star hotel in Lakdikapul offering spacious pillar-free banquet halls, on-site multi-cuisine catering, and convenient family transit.",
                        "capacity_check": "Capacity: 750 guests (Accommodates 400 guests with ~87% buffer)",
                        "budget_breakdown": "Est. Rental: ₹1.8L | F&B Target: ₹950/plate within your ₹800,000 envelope",
                        "why": [
                            "Pragmatic, cost-effective secondary banquet option for pre-wedding ceremonies",
                            "Convenient central location near Hyderabad railway terminal for out-of-town elders"
                        ],
                        "maps_url": "https://maps.google.com/?q=Best+Western+Ashoka+Hyderabad"
                    },
                    {
                        "id": "v3",
                        "title": "Chowmahalla Palace Khilwat Lawns",
                        "affinity": 0.96,
                        "est_cost": 650000,
                        "loved_by_both": True,
                        "status": "done",
                        "description": "Historic UNESCO Asia-Pacific heritage palace lawns surrounded by illuminated yellow stucco facades, fountain courtyards, and antique royal cars.",
                        "capacity_check": "Capacity: 1,200 guests (Spacious grand setting for royal reception)",
                        "budget_breakdown": "Est. Rental: ₹3.2L | F&B Target: ₹1,400/plate",
                        "why": [
                            "Spectacular cinematic backdrop for night receptions and heirloom couple portraits",
                            "Unbeatable cultural prestige honoring your royal celebration vision"
                        ],
                        "maps_url": "https://maps.google.com/?q=Chowmahalla+Palace+Hyderabad"
                    }
                ]
            },
            {
                "key": "decor",
                "title": "Stage, Mandap & Ceremony Floral Spec",
                "status": "ready",
                "summary": "Geometric architectural floral mandap with warm 2700K incandescent lighting and dual-heritage Peshwai-Mughlai aesthetic harmony.",
                "items": [
                    {
                        "id": "d1",
                        "title": "Minimalist Royal Mandap with Floating Jasmine Canopies",
                        "affinity": 0.97,
                        "est_cost": 280000,
                        "loved_by_both": True,
                        "status": "liked",
                        "description": "Four slender brass pillars supporting cascading strands of fragrant Madurai Mogra and blush English roses. Raised teak plinth with low-rise floor seating for family elders.",
                        "lighting_spec": "2700K soft warm incandescent spotlights angled at 45° to eliminate eye-socket shadows on 4K cinematic cameras",
                        "anti_clash_check": "Zero clash: Color palette contrasts against ivory sherwani and ruby bridal silks",
                        "hex_colors": ["#FDFBF7", "#C5A059", "#8E1B38", "#D48B96"],
                        "why": [
                            f"Honors {name2}'s love for authentic jasmine fragrance and clean geometric lines",
                            f"Provides {name1}'s regal brass framework without overpowering the sacred Vedic fire"
                        ]
                    },
                    {
                        "id": "d2",
                        "title": "Haldi Sunshine Canopy with Marigold Ombré Tunnel",
                        "affinity": 0.95,
                        "est_cost": 120000,
                        "status": "done",
                        "description": "Graduated ombré marigold drapes transitioning from pale saffron to deep amber, with hand-painted brass urli vessels filled with rose petals.",
                        "lighting_spec": "Filtered morning sunlight canopy with gold reflector bounce",
                        "hex_colors": ["#FFF176", "#FFB300", "#FF6F00", "#4CAF50"],
                        "why": ["Lively, candid daytime aesthetic perfect for joyful Haldi family photos"]
                    }
                ]
            },
            {
                "key": "sangeet",
                "title": "Sangeet Music Progression",
                "status": "ready",
                "summary": "A 3-act emotional music curve designed to honor both families: acoustic welcome, emotional couple spotlight, and explosive 128 BPM dance finale.",
                "items": [
                    {
                        "id": "m1",
                        "title": "'Kasoor' Acoustic Transitioning into High-BPM Brass Finale",
                        "act": "Act II: Couple First Dance Spotlight",
                        "affinity": 0.98,
                        "loved_by_both": True,
                        "tempo_bpm": "84 → 128 BPM",
                        "vibe_tag": "Romantic Crescendo",
                        "status": "liked",
                        "description": f"Begins with an intimate guitar slow dance for {name1} & {name2}, transitioning smoothly at 1:45 with a surprise brass burst that invites all friends to storm the stage.",
                        "cue_note": "DJ Cue: Low fog haze triggered at 0:40; CO2 jet blast and warm blinders at 1:45 transition",
                        "why": [
                            f"Highlights {name2}'s favorite indie acoustic emotional intimacy",
                            f"Delivers {name1}'s grand energetic celebration moment"
                        ]
                    },
                    {
                        "id": "m2",
                        "title": "Bollywood & Retro Golden Era Medley",
                        "act": "Act I: Grandparents & Family Welcome",
                        "affinity": 0.93,
                        "tempo_bpm": "95 BPM",
                        "vibe_tag": "Nostalgic Joy",
                        "status": "suggested",
                        "description": "Timeless classics by Kishore Kumar, R.D. Burman, and Lata Mangeshkar rearranged with live acoustic percussion so older guests sing along warmly.",
                        "cue_note": "Acoustic volume maintained below 78 dB so guests can converse comfortably over appetizers",
                        "why": ["Ensures grandparents and extended family feel thoroughly included in the celebration"]
                    }
                ]
            },
            {
                "key": "menu",
                "title": "Dual-Heritage Wedding Feast",
                "status": "ready",
                "summary": "Anti-waste culinary curation balancing North Indian royal tandoor and Maharashtrian festive classics with exact portion formulas.",
                "items": [
                    {
                        "id": "f1",
                        "title": "Zafrani Dum Gosht & Dal Bukhara alongside Kolhapuri Tambda Rassa",
                        "course_type": "Main Course",
                        "affinity": 0.96,
                        "est_cost": 420000,
                        "loved_by_both": True,
                        "status": "liked",
                        "description": "Slow-cooked saffron lamb and 24-hour black lentils paired with artisanal Maharashtrian mutton rassa and fresh multi-grain rotis.",
                        "portion_math": "400 guests × 185g protein + 120g lentils = 122kg prepared in 3 staggered batches to reduce waste by ~28%",
                        "anti_clash_check": "Separate dedicated pure-vegetarian and Jain kitchen counters with distinct serving teams",
                        "why": [
                            f"Celebrates {name1}'s heritage with rich Awadhi slow-cooked gravies",
                            f"Honors {name2}'s roots with spicy, authentic Kolhapuri flavors"
                        ]
                    },
                    {
                        "id": "f2",
                        "title": "Signature Cocktail: The Royal Saffron-Citrus Spark",
                        "course_type": "Welcome Bar",
                        "affinity": 0.97,
                        "est_cost": 65000,
                        "status": "done",
                        "description": "Kashmiri saffron syrup, Meyer lemon juice, sparkling elderflower tonic, and crushed star anise served in crystal coupes.",
                        "why": ["Custom couple taste chemistry formulation served as signature welcome drink"]
                    }
                ]
            },
            {
                "key": "outfits",
                "title": "Ceremony-by-Ceremony Outfits & Color Harmony",
                "status": "ready",
                "summary": "Curated designer pairings ensuring bride and groom complement without clashing or blending into backdrop florals.",
                "items": [
                    {
                        "id": "o1",
                        "title": "Wedding Vows: Raw Silk Sherwani & Handwoven Paithani Lehengas",
                        "affinity": 0.98,
                        "est_cost": 380000,
                        "loved_by_both": True,
                        "status": "liked",
                        "description": f"Ivory raw-silk achkan with micro-embroidered gold thread for {name1}, paired with a rich heirloom Crimson & Emerald Paithani woven drape for {name2}.",
                        "bride_groom_pairing": f"{name1}: Ivory & Antique Gold | {name2}: Crimson Red with Peacock Gold Zari border",
                        "hex_colors": ["#FFFFF0", "#D4AF37", "#9E1B32", "#1B4D3E"],
                        "why": [
                            f"Maintains {name1}'s regal royal silhouettes",
                            f"Embodies {name2}'s Maharashtrian bridal heritage with timeless elegance"
                        ]
                    }
                ]
            }
        ]
    }
    await db.document(f"spaces/{space_id}/plans/v1").set(plan_doc)

    # 8. Everyday Plans (Seeded under calendar_items so /app/plans displays 3-column grid)
    plans = [
        {
            "title": "Friday Movie Night: Zindagi Na Milegi Dobara",
            "subtitle": "Netflix Streaming & Spanish Tapas at Home",
            "category": "movie",
            "date": "2026-11-06",
            "time": "20:30",
            "description": f"Cozy living room streaming date for {name1} & {name2} with shared wine, Spanish tapas, and road-trip wanderlust.",
            "is_private": False
        },
        {
            "title": f"Pre-Wedding De-Stressor Date at Olive Bistro ({space_doc['city']})",
            "subtitle": "Lakeside Terrace • Strictly Zero Wedding Talk Tonight",
            "category": "dining",
            "date": "2026-11-14",
            "time": "19:45",
            "description": "Candlelit dinner overlooking Durgam Cheruvu lake. Fresh artisanal sourdough pizza, chilled mocktails, and complete couple recharge.",
            "maps_url": "https://maps.google.com/?q=Olive+Bistro+Hyderabad",
            "is_private": False
        },
        {
            "title": "Spontaneous 48h Nature Retreat to Ananthagiri Hills",
            "subtitle": "Coffee Plantation Cottages • 90 Mins from City",
            "category": "travel",
            "date": "2026-11-21",
            "time": "08:00 AM",
            "description": "A tranquil 2-day digital detox getaway before the festive season: forest morning trails, campfire stargazing, and private downtime.",
            "maps_url": "https://maps.google.com/?q=Ananthagiri+Hills",
            "is_private": False
        }
    ]
    # Clear previous items
    async for csnap in db.collection("calendar_items").where("couple_id", "==", cid).stream():
        await db.document(f"calendar_items/{csnap.id}").delete()
    for p in plans:
        await calendar_svc.add_calendar_item(u1_doc, p)

    # 9. Secret Surprise (Narayan -> Amruta)
    async for ssnap in db.collection("surprises").where("couple_id", "==", cid).stream():
        await db.document(f"surprises/{ssnap.id}").delete()
    surprise_doc = {
        "id": new_id("sp"),
        "owner_uid": uid1,
        "couple_id": cid,
        "for_name": name2,
        "occasion": "Pre-Wedding Surprise Gift",
        "date": "2026-12-05",
        "notes": f"Planned privately by {name1} using {name2}'s hidden love for French jasmine perfumes.",
        "ideas": [
            {
                "title": f"Artisanal Jasmine & Sandalwood Discovery Kit for {name2}",
                "description": "Bespoke perfume atelier set custom-blended using Madurai Sambac jasmine and Mysore sandalwood, engraved with wedding date.",
                "why": f"Matches {name2}'s private taste in clean French florals with sacred Indian heritage notes."
            }
        ],
        "created_at": now_iso()
    }
    await db.document(f"surprises/{surprise_doc['id']}").set(surprise_doc)

    # 10. Clean Realistic Chat Conversation
    chat_turns = [
        {
            "id": "turn_1",
            "role": "agent",
            "text": f"Hello {name1}! 💕 Welcome to cupl.ai — your AI concierge for life together.\n\nI'm here to help you and {name2} navigate life's big milestones and everyday dates with deep cultural taste intelligence. Would you like a quick tour of how I can assist you, or is there an upcoming celebration on your mind?",
            "created_at": now_iso()
        },
        {
            "id": "turn_2",
            "role": "user",
            "text": f"Hi! Yes, we are planning our Royal Wedding in Hyderabad for 400 guests in December. {name2} and I want it to be unforgettable.",
            "created_at": now_iso()
        },
        {
            "id": "turn_3",
            "role": "agent",
            "text": f"Hyderabad in December is pure royalty, {name1}! 👑\n\nTo ensure our recommendations are powered by real cultural taste intelligence, tell me: what musical vibe and culinary flavors make you feel most alive?",
            "created_at": now_iso()
        },
        {
            "id": "turn_4",
            "role": "user",
            "text": "I love grand Awadhi biryani, Arijit Singh melodies, and majestic heritage architecture. But Amruta loves indie acoustic music and Maharashtrian Peshwai traditions.",
            "created_at": now_iso()
        },
        {
            "id": "turn_5",
            "role": "agent",
            "text": f"That combination is magical — North Indian royal grandeur meets Maharashtrian poetic elegance! ✨\n\nI've woven your masterplan with verified 750-guest venues, anti-waste portioning math, and a dual-heritage Sangeet curve. Plus, I've scheduled your Friday movie night and Olive Bistro date in your Plans tab!",
            "created_at": now_iso()
        }
    ]
    await db.document(f"conversations/{uid1}").set({
        "turn_count": 5,
        "summary": f"{name1} and {name2} are planning a 400-guest Royal Wedding in Hyderabad blending Awadhi and Maharashtrian heritage. Wedding plan v1 woven and everyday plans scheduled.",
        "turns": chat_turns,
        "updated_at": now_iso()
    })

    print(f"\n[SUCCESS] Pristine showcase couple created:")
    print(f" - Partner 1 Login Token: dev-{uid1} ({name1})")
    print(f" - Partner 2 Login Token: dev-{uid2} ({name2})")
    print(f" - Couple ID: {cid}")
    print(f" - Event Space: {space_id} ({space_doc['title']})")
    print(f" - Everyday Plans: 3 seeded")
    print(f" - Secret Surprise: 1 seeded")
    print(f" - Chat History: 5 turns with cupl AI")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--name1", default="Narayan", help="Partner 1 Name")
    parser.add_argument("--name2", default="Amruta", help="Partner 2 Name")
    parser.add_argument("--prefix", default="showcase", help="Unique ID prefix")
    args = parser.parse_args()
    asyncio.run(create_showcase(args.name1, args.name2, args.prefix))
