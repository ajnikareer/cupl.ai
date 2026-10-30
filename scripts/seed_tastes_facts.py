import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("."))
from backend.app.db import db, new_id, now_iso

async def seed_facts():
    print("Seeding rich facts/tastes into users/narayan/facts and users/amruta/facts...")

    narayan_facts = [
        # Music
        {"category": "music", "text": "Arijit Singh", "sentiment": 1.0, "visibility": "shared", "image": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=200&q=80"},
        {"category": "music", "text": "Acoustic Sufi & Soulful Strings", "sentiment": 1.0, "visibility": "shared"},
        {"category": "music", "text": "Nusrat Fateh Ali Khan", "sentiment": 0.95, "visibility": "shared"},
        {"category": "music", "text": "Blaring Nightclub EDM", "sentiment": -0.9, "visibility": "shared"},
        # Dining / Place
        {"category": "place", "text": "Royal Awadhi Dum Biryani", "sentiment": 1.0, "visibility": "shared", "image": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=200&q=80"},
        {"category": "place", "text": "Mughlai Galouti Kebabs", "sentiment": 0.95, "visibility": "shared"},
        {"category": "place", "text": "Taj Falaknuma Adaa Courtyard", "sentiment": 1.0, "visibility": "shared"},
        # Fashion
        {"category": "fashion", "text": "Sabyasachi Raw-Silk Sherwani", "sentiment": 1.0, "visibility": "shared"},
        {"category": "fashion", "text": "Ivory & Dull Gold Zardozi Weaves", "sentiment": 0.9, "visibility": "shared"},
        # Travel
        {"category": "travel", "text": "Amalfi Coast & Southern Italy", "sentiment": 0.9, "visibility": "shared"},
        {"category": "travel", "text": "Udaipur Royal Lake Palaces", "sentiment": 0.95, "visibility": "shared"},
        # Film
        {"category": "film", "text": "Zindagi Na Milegi Dobara", "sentiment": 1.0, "visibility": "shared"},
        {"category": "film", "text": "Yeh Jawaani Hai Deewani", "sentiment": 0.9, "visibility": "shared"}
    ]

    for f in narayan_facts:
        fid = new_id("f")
        doc = {
            "id": fid,
            "category": f["category"],
            "text": f["text"],
            "image": f.get("image"),
            "sentiment": f["sentiment"],
            "confidence": 0.95,
            "visibility": f["visibility"],
            "source": "chat",
            "resolution": "resolved",
            "created_at": now_iso(),
            "updated_at": now_iso()
        }
        await db.document(f"users/narayan/facts/{fid}").set(doc)

    amruta_facts = [
        # Music
        {"category": "music", "text": "Classical Carnatic Acoustic Fusion", "sentiment": 1.0, "visibility": "shared"},
        {"category": "music", "text": "Prateek Kuhad", "sentiment": 0.95, "visibility": "shared"},
        {"category": "music", "text": "Anoushka Shankar Sitar", "sentiment": 0.9, "visibility": "shared"},
        # Dining / Place
        {"category": "place", "text": "Coastal Andhra Spiced Seafood", "sentiment": 1.0, "visibility": "shared"},
        {"category": "place", "text": "Artisanal South Indian Filter Coffee", "sentiment": 1.0, "visibility": "shared"},
        {"category": "place", "text": "Overly Processed Commercial Buffets", "sentiment": -0.85, "visibility": "shared"},
        # Fashion
        {"category": "fashion", "text": "Raw Mango Handwoven Kanjeevarams", "sentiment": 1.0, "visibility": "shared"},
        {"category": "fashion", "text": "Rose-Gold & Pastel Silk Lehengas", "sentiment": 0.95, "visibility": "shared"},
        # Travel
        {"category": "travel", "text": "Uluwatu Sunset Cliffs & Bali Rainforest", "sentiment": 1.0, "visibility": "shared"},
        {"category": "travel", "text": "Kyoto Zen Gardens", "sentiment": 0.9, "visibility": "shared"},
        # Film
        {"category": "film", "text": "Barfi!", "sentiment": 1.0, "visibility": "shared"},
        {"category": "film", "text": "Piku", "sentiment": 0.9, "visibility": "shared"}
    ]

    for f in amruta_facts:
        fid = new_id("f")
        doc = {
            "id": fid,
            "category": f["category"],
            "text": f["text"],
            "image": f.get("image"),
            "sentiment": f["sentiment"],
            "confidence": 0.95,
            "visibility": f["visibility"],
            "source": "chat",
            "resolution": "resolved",
            "created_at": now_iso(),
            "updated_at": now_iso()
        }
        await db.document(f"users/amruta/facts/{fid}").set(doc)

    print("Successfully seeded all facts for Narayan & Amruta!")

if __name__ == "__main__":
    asyncio.run(seed_facts())

