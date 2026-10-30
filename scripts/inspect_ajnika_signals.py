import asyncio
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "backend")

from backend.app.config import settings
settings.QLOO_API_KEY = "hack_2e9a0b569f352f79299887692053d2cae44c293c"

from backend.app.db import db
from backend.app.services import qloo
from backend.app.services.spaces import TEMPLATES

async def inspect_ajnika():
    facts = []
    async for f in db.collection("facts").where("uid", "==", "ajnikarnarayan").stream():
        facts.append(f.to_dict())
    print("FACTS COUNT:", len(facts))
    for f in facts:
        print(f"Fact: [{f.get('category')}] {f.get('text')} | entity_id: {f.get('entity_id')} | tag_id: {f.get('tag_id')} | sentiment: {f.get('sentiment')}")

    # Now let's see what signals(facts) produces
    from backend.app.services.plan_engine import signals
    sig = signals(facts)
    print("\nSIGNALS:", sig)

    # Now let's see what QLOO blend produces for each section of prewedding:
    tmpl = TEMPLATES["prewedding"]
    for sec in tmpl["sections"]:
        if sec["kind"] == "qloo":
            print(f"\n--- TESTING BLEND FOR {sec['title']} (qtype={sec['qtype']}) ---")
            loc = "Hyderabad" if sec.get("location_field") == "city" else None
            res = await qloo.blend(sec["qtype"], {"ajnikarnarayan": sig}, loc, sec["take"])
            print(f"Candidates count: {len(res)}")
            for c in res[:6]:
                print(f"  * {c.get('name')} (id: {c.get('entity_id')}) | tags: {c.get('tags')[:3] if c.get('tags') else []}")

asyncio.run(inspect_ajnika())

