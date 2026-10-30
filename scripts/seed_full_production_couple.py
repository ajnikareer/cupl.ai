import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("."))

from backend.app.db import db, new_id, now_iso

async def seed_master_profiles():
    print("Beginning seeding of fully loaded production profiles for Narayan & Amruta...")

    uid1 = "narayan"
    uid2 = "amruta"
    cid = "c_narayan_amruta"
    space_wedding = "s_wedding"
    space_prewedding = "s_prewedding"
    space_engagement = "s_engagement"
    space_honeymoon = "s_honeymoon"
    space_trip = "s_trip"

    # ---------------- 1. GROOM: NARAYAN ----------------
    print("Seeding Groom (Narayan)...")
    narayan_doc = {
        "uid": uid1,
        "name": "Narayan",
        "name_confirmed": True,
        "name_from_provider": True,
        "email": "narayan@cupl.app",
        "couple_id": cid,
        "active_space_id": space_wedding,
        "profile": {
            "partner_name": "Amruta",
            "how_met": "Met at an independent coffee roastery in Jubilee Hills",
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
    await db.document(f"users/{uid1}").set(narayan_doc)

    # ---------------- 2. BRIDE: AMRUTA ----------------
    print("Seeding Bride (Amruta)...")
    amruta_doc = {
        "uid": uid2,
        "name": "Amruta",
        "name_confirmed": True,
        "name_from_provider": True,
        "email": "amruta@cupl.app",
        "couple_id": cid,
        "active_space_id": space_wedding,
        "profile": {
            "partner_name": "Narayan",
            "how_met": "Met at an independent coffee roastery in Jubilee Hills",
            "heritage": "South Indian Telugu & Coastal",
            "tradition": "Hindu (Traditional South Indian rituals & Pellikuthuru)",
            "state": "Hyderabad",
            "country": "India",
            "greeted": True,
            "invite_offered": True,
            "partner_welcomed": True
        },
        "created_at": now_iso()
    }
    await db.document(f"users/{uid2}").set(amruta_doc)

    # ---------------- 3. COUPLE DOCUMENT & TASTES DNA ----------------
    print("Seeding Couple & Tastes DNA...")
    couple_doc = {
        "id": cid,
        "members": [uid1, uid2],
        "status": "engaged",
        "recommends_enabled": True,
        "recommends_cycle": 0,
        "created_at": now_iso(),
        "dna": {
            "vibe": "Royal North Indian Grandeur meets Coastal South Indian Intimacy",
            "description": "An authentic cultural tapestry blending Narayan's appreciation for regal Awadhi heritage and grand acoustic melodies with Amruta's love for classical Carnatic textures, handwoven Kanjeevarams, and coastal cuisine.",
            "affinity_score": 0.88,
            "shared": [
                {"name": "Acoustic Sufi & Soulful Strings", "category": "music"},
                {"name": "Heritage Courtyard Dining", "category": "dining"},
                {"name": "Zindagi Na Milegi Dobara", "category": "movie"},
                {"name": "Barfi!", "category": "movie"},
                {"name": "Sabyasachi & Raw Mango Handlooms", "category": "fashion"},
                {"name": "Uluwatu Cliffs & Bali Coast", "category": "travel"},
                {"name": "Artisanal Filter Coffee & Slow Mornings", "category": "lifestyle"}
            ],
            "cultural_harmony": {
                "title": "Awadhi-Telugu Royal Dual-Heritage Harmony",
                "summary": "Seamlessly synchronizing Amruta's gold-bordered Kanjeevaram Haldi/Pellikuthuru rituals with Narayan's regal Baraat and Awadhi dum cuisine.",
                "ideas": [
                    {"category": "Ceremony", "title": "Bilingual Vows & Regal Mandap", "description": "Traditional Vedic chants paired with personalized Hindi and Telugu vows under a 2700K warm floral canopy."},
                    {"category": "Catering", "title": "Dual-Tradition Anti-Waste Gastronomy", "description": "Parallel live culinary counters: Awadhi Zafrani Biryani alongside authentic Andhra Royyala Vepudu and Pootharekulu."},
                    {"category": "Sangeet", "title": "Multi-Generational Energy Curve", "description": "100 BPM acoustic Sufi transitions into 118 BPM Telugu-Hindi hits and a peak 130 BPM Bollywood-Dhol dance finale."}
                ]
            }
        }
    }
    await db.document(f"couples/{cid}").set(couple_doc)

    # ---------------- 4. TASTES FOR NARAYAN & AMRUTA ----------------
    print("Seeding Taste Profiles...")
    narayan_tastes = [
        {"text": "Arijit Singh & Soulful Bollywood", "category": "music", "sentiment": 1.0, "visibility": "shared"},
        {"text": "Acoustic Sufi & Nusrat Fateh Ali Khan", "category": "music", "sentiment": 1.0, "visibility": "shared"},
        {"text": "Royal Awadhi Dum Biryani", "category": "food", "sentiment": 1.0, "visibility": "shared"},
        {"text": "Mughlai Galouti Kebabs", "category": "food", "sentiment": 0.9, "visibility": "shared"},
        {"text": "Sabyasachi Raw-Silk Sherwani", "category": "fashion", "sentiment": 1.0, "visibility": "shared"},
        {"text": "Amalfi Coast & Southern Italy", "category": "travel", "sentiment": 0.85, "visibility": "shared"},
        {"text": "Zindagi Na Milegi Dobara", "category": "film", "sentiment": 1.0, "visibility": "shared"},
        {"text": "Extremely Loud Nightclub DJs", "category": "music", "sentiment": -0.9, "visibility": "shared"}
    ]
    for t in narayan_tastes:
        await db.document(f"users/{uid1}/tastes/{new_id('t')}").set({**t, "created_at": now_iso()})

    amruta_tastes = [
        {"text": "Classical Carnatic Acoustic Fusion", "category": "music", "sentiment": 1.0, "visibility": "shared"},
        {"text": "Prateek Kuhad & Indie Melodies", "category": "music", "sentiment": 0.95, "visibility": "shared"},
        {"text": "Coastal Andhra Prawn Curry & Spiced Seafood", "category": "food", "sentiment": 1.0, "visibility": "shared"},
        {"text": "South Indian Filter Coffee", "category": "food", "sentiment": 1.0, "visibility": "shared"},
        {"text": "Raw Mango Handwoven Kanjeevaram Silks", "category": "fashion", "sentiment": 1.0, "visibility": "shared"},
        {"text": "Uluwatu Sunset Cliffs & Bali Rainforest", "category": "travel", "sentiment": 1.0, "visibility": "shared"},
        {"text": "Barfi! & Heartwarming Cinema", "category": "film", "sentiment": 0.9, "visibility": "shared"},
        {"text": "Overly Processed Buffets", "category": "food", "sentiment": -0.85, "visibility": "shared"}
    ]
    for t in amruta_tastes:
        await db.document(f"users/{uid2}/tastes/{new_id('t')}").set({**t, "created_at": now_iso()})

    # ---------------- 5. ALL 5 EVENT SPACES WITH FULL MASTERPLANS ----------------
    print("Seeding 5 Milestone Event Spaces and Masterplans...")

    # A. WEDDING (Royal Hyderabad Wedding)
    wedding_space = {
        "id": space_wedding,
        "couple_id": cid,
        "type": "wedding",
        "title": "Royal Hyderabad Wedding",
        "city": "Hyderabad",
        "start_date": "2026-12-18",
        "end_date": "2026-12-20",
        "guests": 400,
        "budget": 2500000,
        "currency": "INR",
        "state": "planned",
        "active_plan_version": 1,
        "created_by": uid1,
        "created_at": now_iso()
    }
    await db.document(f"spaces/{space_wedding}").set(wedding_space)

    wedding_plan = {
        "version": 1,
        "status": "ready",
        "created_at": now_iso(),
        "summary": "Dual-heritage royal wedding masterplan harmonizing Awadhi luxury with South Indian Telugu traditions for 400 guests within ₹25L.",
        "sections": [
            {
                "key": "venue",
                "title": "Venue Shortlist",
                "summary": "Verified against 400-guest capacity and ₹8L venue budget envelope.",
                "items": [
                    {
                        "id": "v1",
                        "title": "Best Western Ashoka (Hotel & AC Banquets)",
                        "description": "Central 3-star property in Lakdikapul offering pillarless banquet halls for up to 750 guests with in-house Awadhi and South Indian catering facilities.",
                        "affinity": 0.94,
                        "est_cost": 800000,
                        "capacity_check": "Capacity: 750 guests (Comfortably accommodates 400 guests with 87% buffer).",
                        "budget_breakdown": "Rental: ₹3.5L | F&B Target: ₹1,125/plate within ₹800,000 envelope.",
                        "status": "done"
                    },
                    {
                        "id": "v2",
                        "title": "Fort Grand Royal Heritage Lawns, Shamshabad",
                        "description": "Regal sandstone archways and sprawling manicured lawns ideal for grand Baraat processions and bilingual Vedic mandaps.",
                        "affinity": 0.91,
                        "est_cost": 850000,
                        "capacity_check": "Capacity: 1200 guests (Spacious outdoor lawns with breezy evening ventilation).",
                        "budget_breakdown": "Rental: ₹4.5L | F&B Target: ₹1,000/plate.",
                        "status": "liked"
                    }
                ]
            },
            {
                "key": "ceremonies",
                "title": "Stage & Mandap Decoration Themes",
                "summary": "Architectural mandap concepts with 2700K warm lighting and zero-clash palettes.",
                "items": [
                    {
                        "id": "c1",
                        "title": "The Awadhi-Telugu Golden Blossom Mandap",
                        "description": "Open-air floral pavilion featuring suspended marigolds, night-blooming tuberose, and burnished brass kalash urns, illuminated by 2700K warm candlelight.",
                        "affinity": 0.95,
                        "est_cost": 300000,
                        "lighting_spec": "2700K warm cinematic lighting with zero strobe glares for photography.",
                        "hex_colors": ["#C49A45", "#800020", "#FFF8EE"],
                        "status": "done"
                    }
                ]
            },
            {
                "key": "sangeet",
                "title": "Curated Song & Music Blueprint",
                "summary": "Multi-generational energy curve balancing acoustic Sufi with peak Bollywood-Dhol dance tracks.",
                "items": [
                    {
                        "id": "s1",
                        "title": "Acoustic Sufi Cocktail Entry (95 BPM)",
                        "description": "Live sarangi and acoustic guitar rendition of 'Kesariya' and 'Kun Faya Kun' welcoming elders and arriving guests.",
                        "affinity": 0.96,
                        "cue_note": "Choreography Cue: Fade gently as couple takes the stage for ring exchange.",
                        "status": "done"
                    },
                    {
                        "id": "s2",
                        "title": "High-Energy Couple & Friends Finale (128 BPM)",
                        "description": "Seamless transition from Telugu energetic hits into Bollywood dance bangers ('Galla Goodiyan', 'Kala Chashma').",
                        "affinity": 0.93,
                        "cue_note": "DJ Cue: Full brass drops with live Dhol percussion at 23:15.",
                        "status": "liked"
                    }
                ]
            },
            {
                "key": "menu",
                "title": "Anti-Waste Dual-Tradition Catering",
                "summary": "Structured culinary courses balancing Awadhi Dum Biryani with Coastal Andhra specialties.",
                "items": [
                    {
                        "id": "m1",
                        "title": "Parallel Heritage Culinary Counters",
                        "description": "Live Awadhi Dum Biryani and Galouti Kebab counter paired with authentic Coastal Andhra Royyala Vepudu, Gongura Mamsam, and steaming Ghee Idlis.",
                        "affinity": 0.95,
                        "est_cost": 625000,
                        "portion_math": "Dynamic 380-plate base with 10% rolling live kitchen replenishment, saving ~₹75,000 in surplus food waste.",
                        "status": "done"
                    }
                ]
            },
            {
                "key": "outfits",
                "title": "Ceremony Outfits & Color Harmony",
                "summary": "Designer attire pairings with zero-backdrop clash check.",
                "items": [
                    {
                        "id": "o1",
                        "title": "Sabyasachi Raw-Silk & Raw Mango Kanjeevaram Harmony",
                        "description": "Narayan in ivory raw-silk sherwani with dull-gold zardozi; Amruta in handwoven vermilion and rose-gold Kanjeevaram silk.",
                        "affinity": 0.96,
                        "bride_groom_pairing": "Ivory/Gold Sherwani perfectly complements Vermilion/Rose-Gold Silk without backdrop clash.",
                        "anti_clash_check": "Guaranteed contrast against marigold-gold mandap arches.",
                        "hex_colors": ["#FFFDD0", "#E34234", "#D4AF37"],
                        "status": "done"
                    }
                ]
            }
        ]
    }
    await db.document(f"spaces/{space_wedding}/plans/v1").set(wedding_plan)

    # B. PREWEDDING (Udaipur Heritage Palace Shoot)
    prewedding_space = {
        "id": space_prewedding,
        "couple_id": cid,
        "type": "prewedding",
        "title": "Prewedding Shoot",
        "city": "Udaipur",
        "start_date": "2026-10-15",
        "end_date": "2026-10-17",
        "budget": 400000,
        "currency": "INR",
        "state": "planned",
        "active_plan_version": 1,
        "created_by": uid1,
        "created_at": now_iso()
    }
    await db.document(f"spaces/{space_prewedding}").set(prewedding_space)
    await db.document(f"spaces/{space_prewedding}/plans/v1").set({
        "version": 1,
        "status": "ready",
        "created_at": now_iso(),
        "summary": "Udaipur regal lake palace and sunset photography shoot capturing royal heritage styling.",
        "sections": [
            {
                "key": "venues",
                "title": "Scenic Photography Locations",
                "items": [
                    {
                        "id": "pw1",
                        "title": "Lake Pichola Sunset Boat & Ghats",
                        "description": "Golden-hour boat shoot against the floating Lake Palace with natural acoustic breeze reflections.",
                        "affinity": 0.97,
                        "status": "done"
                    }
                ]
            }
        ]
    })

    # C. ENGAGEMENT (Ring Ceremony & Cocktail Night)
    engagement_space = {
        "id": space_engagement,
        "couple_id": cid,
        "type": "engagement",
        "title": "Engagement & Cocktail Night",
        "city": "Hyderabad",
        "start_date": "2026-11-20",
        "budget": 800000,
        "currency": "INR",
        "state": "planned",
        "active_plan_version": 1,
        "created_by": uid1,
        "created_at": now_iso()
    }
    await db.document(f"spaces/{space_engagement}").set(engagement_space)
    await db.document(f"spaces/{space_engagement}/plans/v1").set({
        "version": 1,
        "status": "ready",
        "created_at": now_iso(),
        "summary": "Intimate ring ceremony and cocktail celebration at Taj Falaknuma Palace courtyard.",
        "sections": [
            {
                "key": "cocktail",
                "title": "Cocktail Formulations & Live Jazz",
                "items": [
                    {
                        "id": "ec1",
                        "title": "Adaa Courtyard Live Sitar-Jazz Ensemble",
                        "description": "Contemporary sitar and upright bass playing acoustic fusion under starlit palace arches.",
                        "affinity": 0.95,
                        "status": "done"
                    }
                ]
            }
        ]
    })

    # D. HONEYMOON (Bali Tropical Romantic Escape)
    honeymoon_space = {
        "id": space_honeymoon,
        "couple_id": cid,
        "type": "honeymoon",
        "title": "Bali Romantic Honeymoon",
        "destination": "Bali, Indonesia",
        "start_date": "2027-01-10",
        "end_date": "2027-01-20",
        "budget": 700000,
        "currency": "INR",
        "state": "planned",
        "active_plan_version": 1,
        "created_by": uid1,
        "created_at": now_iso()
    }
    await db.document(f"spaces/{space_honeymoon}").set(honeymoon_space)
    await db.document(f"spaces/{space_honeymoon}/plans/v1").set({
        "version": 1,
        "status": "ready",
        "created_at": now_iso(),
        "summary": "10-day slow-paced romantic honeymoon balancing Uluwatu sunset ocean cliffs with Ubud rainforest wellness.",
        "sections": [
            {
                "key": "destinations",
                "title": "Ranked Destination Match",
                "items": [
                    {
                        "id": "h1",
                        "title": "Six Senses Uluwatu Cliffside Pool Villa",
                        "description": "Private infinity pool villa suspended over the Indian Ocean with direct sunset views and private butler.",
                        "affinity": 0.98,
                        "status": "done"
                    }
                ]
            }
        ]
    })

    # E. TRIP (Tuscan Wine & Culinary Escape)
    trip_space = {
        "id": space_trip,
        "couple_id": cid,
        "type": "trip",
        "title": "Tuscan Wine & Culinary Escape",
        "city": "Florence & Chianti",
        "start_date": "2027-04-12",
        "end_date": "2027-04-18",
        "budget": 600000,
        "currency": "INR",
        "state": "planned",
        "active_plan_version": 1,
        "created_by": uid1,
        "created_at": now_iso()
    }
    await db.document(f"spaces/{space_trip}").set(trip_space)
    await db.document(f"spaces/{space_trip}/plans/v1").set({
        "version": 1,
        "status": "ready",
        "created_at": now_iso(),
        "summary": "Countryside villa retreat, Chianti vineyard tastings, and private pasta masterclass.",
        "sections": [
            {
                "key": "experiences",
                "title": "Curated Wine & Culinary Experiences",
                "items": [
                    {
                        "id": "t1",
                        "title": "Private Chianti Vineyard Tasting & Truffle Masterclass",
                        "description": "Exclusive estate tour in Greve in Chianti with private sommelier pairing.",
                        "affinity": 0.94,
                        "status": "done"
                    }
                ]
            }
        ]
    })

    # ---------------- 6. 4 CUSTOM PLANS UNDER 'OUR PLANS' ----------------
    print("Seeding 4 Custom Plans in Our Plans...")
    custom_plans = [
        {
            "id": "plan_bali",
            "couple_id": cid,
            "title": "Bali Romantic Honeymoon Masterplan",
            "category": "travel",
            "date": "2027-01-10",
            "time": "14:00",
            "description": "10-day tropical escape: 5 nights Uluwatu cliff villa + 5 nights Ubud rainforest sanctuary with private sunset catamaran.",
            "image": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=800&q=80",
            "is_private": False,
            "created_at": now_iso()
        },
        {
            "id": "plan_sangeet",
            "couple_id": cid,
            "title": "Sangeet 3-Phase Music Curve & Choreography Blueprint",
            "category": "music",
            "date": "2026-12-19",
            "time": "19:30",
            "description": "18 curated tracks with tempo progression from 95 BPM acoustic Sufi to 128 BPM Bollywood-Dhol peak finale.",
            "image": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=800&q=80",
            "is_private": False,
            "created_at": now_iso()
        },
        {
            "id": "plan_decor",
            "couple_id": cid,
            "title": "Living Room Decor Palette & Teak Wood Styling",
            "category": "lifestyle",
            "date": "2026-11-28",
            "time": "11:00",
            "description": "Harmonized aesthetic: Warm Ivory, Terracotta accents, natural Teak Wood, and 2700K ambient architectural lighting.",
            "image": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&w=800&q=80",
            "is_private": False,
            "created_at": now_iso()
        },
        {
            "id": "plan_dinner",
            "couple_id": cid,
            "title": "Friday Pre-Wedding De-Stressor Courtyard Date",
            "category": "dining",
            "date": "2026-11-14",
            "time": "20:00",
            "description": "Romantic courtyard dining at Taj Falaknuma Adaa with live classical sitar and Awadhi tasting menu.",
            "image": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80",
            "is_private": False,
            "created_at": now_iso()
        }
    ]
    for cp in custom_plans:
        await db.document(f"calendar_items/{cp['id']}").set(cp)

    # ---------------- 7. PRIVATE SURPRISES ----------------
    print("Seeding Private Surprises Vault...")
    # Surprise for Amruta by Narayan
    s1 = {
        "id": "surp_heli",
        "owner_uid": uid1,
        "couple_id": cid,
        "for_name": "Amruta",
        "occasion": "Birthday & Anniversary Secret Celebration",
        "date": "2026-12-05",
        "notes": "She loves coastal sunsets and acoustic strings.",
        "ideas": [
            {"title": "Private Sunset Helicopter Flight & Vineyard Dinner", "description": "Charter flight over the hills landing at a private vineyard for candlelit dinner.", "why": "Matches her desire for intimate romantic escapes and panoramic viewpoints."},
            {"title": "Custom Handcrafted Heirloom Bridal Clutch", "description": "Custom zardozi clutch with her initials and coordinates of where we met.", "why": "High aesthetic overlap with her appreciation for artisanal craftsmanship."}
        ],
        "created_at": now_iso()
    }
    await db.document(f"surprises/{s1['id']}").set(s1)

    # Surprise for Narayan by Amruta
    s2 = {
        "id": "surp_watch",
        "owner_uid": uid2,
        "couple_id": cid,
        "for_name": "Narayan",
        "occasion": "Wedding Morning Groom Gift",
        "date": "2026-12-18",
        "notes": "He loves classic timepieces and vintage aesthetics.",
        "ideas": [
            {"title": "Bespoke Engraved Vintage Chronograph Watch", "description": "Classic gold-accent mechanical watch with engraved wedding vows on the caseback.", "why": "Matches his classic royal styling and love for timeless heirloom pieces."}
        ],
        "created_at": now_iso()
    }
    await db.document(f"surprises/{s2['id']}").set(s2)

    # ---------------- 8. REAL CONVERSATION TURNS IN FIRESTORE ----------------
    print("Seeding Conversation Turns in Firestore...")
    turns = [
        {"role": "user", "text": "Hi cupl AI! I am Narayan, planning our royal wedding with my bride Amruta in Hyderabad for December with 400 guests and 25 lakhs budget.", "ts": "2026-10-30T10:00:00Z"},
        {"role": "agent", "text": "Congratulations Narayan! That's wonderful news. A royal Hyderabad wedding with 400 guests and a ₹25L envelope sounds absolutely magnificent. I've created your Wedding Space.\n\nTo ensure our taste intelligence reflects who you are, tell me about your cultural roots, favorite music, dining preferences, and ceremony styling.", "ts": "2026-10-30T10:00:15Z"},
        {"role": "user", "text": "My heritage is Royal North Indian Awadhi. I love grand Awadhi dum biryani, soulful Arijit Singh melodies, and acoustic Sufi music. For outfits, classic ivory raw-silk sherwani.", "ts": "2026-10-30T10:01:00Z"},
        {"role": "agent", "text": "I have locked in your Awadhi heritage, acoustic Sufi melodies, and authentic Awadhi culinary tastes into your taste profile! When Amruta joins, our Couple Gatekeeper will harmonize her tastes with yours to weave the masterplan.", "ts": "2026-10-30T10:01:25Z"},
        {"role": "user", "text": "Amruta has joined! Her heritage is South Indian Telugu. She loves classical Carnatic fusion, coastal Andhra seafood, and handwoven Kanjeevarams.", "ts": "2026-10-30T10:02:00Z"},
        {"role": "agent", "text": "Incredible! With both partner profiles captured, our Couple Gatekeeper has unlocked your full dual-tradition Masterplan with an 88% aesthetic harmony! You can explore the Venue Shortlist, Anti-Waste Catering, and Sangeet curves in your Events space.", "ts": "2026-10-30T10:02:40Z"}
    ]
    for idx, t in enumerate(turns):
        await db.document(f"conversations/{uid1}/turns/m_{idx}").set(t)
        await db.document(f"conversations/{uid2}/turns/m_{idx}").set(t)

    print("\nMaster seeding completed successfully for both Narayan and Amruta!")

if __name__ == "__main__":
    asyncio.run(seed_master_profiles())

